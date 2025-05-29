# Sneekstore/botstore/db.py
import aiomysql
import asyncio
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, host, port, user, password, db):
        self.pool = None
        self.config = dict(host=host, port=port, user=user, password=password, db=db, autocommit=True)

    # Підключення до бази даних
    async def connect(self):
        self.pool = await aiomysql.create_pool(**self.config)
        await self.create_tables()

    # Закриття з'єднання
    async def close(self):
        self.pool.close()
        await self.pool.wait_closed()

    # Створення таблиць
    async def create_tables(self):
        async with self.pool.acquire() as conn:
            # Відключаємо виведення попереджень
            async with conn.cursor() as cur:
                # Вимкнення попереджень
                await cur.execute("SET sql_notes = 0")
                
                try:
                    # Таблиця користувачів
                    await cur.execute("""
                        CREATE TABLE IF NOT EXISTS users (
                            user_id BIGINT PRIMARY KEY,
                            username VARCHAR(64) NOT NULL,
                            balance DECIMAL(15,2) DEFAULT 0.00,
                            purchases INT DEFAULT 0,
                            status VARCHAR(32) DEFAULT 'user',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    # Оновлення для існуючої таблиці
                    try:
                        await cur.execute("ALTER TABLE users MODIFY COLUMN status VARCHAR(32) DEFAULT 'user'")
                    except Exception:
                        pass
                    
                    # Додаємо статус для старих таблиць
                    try:
                        await cur.execute("""
                            ALTER TABLE users 
                            ADD COLUMN status ENUM('user', 'admin') DEFAULT 'user'
                        """)
                    except Exception:
                        pass
                    
                    # Таблиця продажів
                    await cur.execute("""
                        CREATE TABLE IF NOT EXISTS sales (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            user_id BIGINT NOT NULL,
                            brand VARCHAR(32) NOT NULL,
                            model VARCHAR(64) NOT NULL,
                            size VARCHAR(8) NOT NULL,
                            price DECIMAL(15,2) NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                        )
                    """)
                    
                    # Оновлюємо існуючу колонку price в sales
                    try:
                        await cur.execute("ALTER TABLE sales MODIFY COLUMN price DECIMAL(15,2) NOT NULL")
                    except Exception:
                        pass
                    
                    # Таблиця заявок на поповнення
                    await cur.execute("""
                        CREATE TABLE IF NOT EXISTS payment_orders (
                            order_id VARCHAR(20) PRIMARY KEY,
                            user_id BIGINT NOT NULL,
                            amount DECIMAL(15,2) NOT NULL,
                            status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
                            payment_method ENUM('card', 'crypto') DEFAULT 'card',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                        )
                    """)
                    
                    # Додаємо колонку payment_method, якщо вона ще не існує
                    try:
                        await cur.execute("""
                            ALTER TABLE payment_orders 
                            ADD COLUMN payment_method ENUM('card', 'crypto') DEFAULT 'card'
                        """)
                        logger.info("Додана колонка payment_method в таблицю payment_orders")
                    except Exception:
                        pass
                    
                    # Оновлюємо існуючу колонку amount в payment_orders
                    try:
                        await cur.execute("ALTER TABLE payment_orders MODIFY COLUMN amount DECIMAL(15,2) NOT NULL")
                    except Exception:
                        pass
                        
                finally:
                    # Відновлюємо виведення попереджень
                    await cur.execute("SET sql_notes = 1")

    # Створення користувача
    async def create_user(self, user_id, username):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(
                        "INSERT IGNORE INTO users (user_id, username, balance, purchases, status) VALUES (%s, %s, 0, 0, 'user')",
                        (user_id, username)
                    )
                except Exception:
                    await cur.execute(
                        "INSERT IGNORE INTO users (user_id, username, balance, purchases) VALUES (%s, %s, 0, 0)",
                        (user_id, username)
                    )

    # Отримання даних аккаунту
    async def get_account(self, user_id):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT balance, purchases FROM users WHERE user_id=%s", (user_id,))
                row = await cur.fetchone()
                if row:
                    return {"balance": row[0], "purchases": row[1]}
                return {"balance": 0, "purchases": 0}

    # Оновлення балансу
    async def update_balance(self, user_id, amount):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("UPDATE users SET balance=balance+%s WHERE user_id=%s", (amount, user_id))

    # Додавання покупки
    async def add_purchase(self, user_id, price):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("UPDATE users SET balance=balance-%s, purchases=purchases+1 WHERE user_id=%s", (price, user_id))

    # Додавання продажу
    async def add_sale(self, user_id, brand, model, size, price):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT INTO sales (user_id, brand, model, size, price) VALUES (%s, %s, %s, %s, %s)",
                    (user_id, brand, model, size, price)
                )

    # Обробка покупки
    async def process_purchase(self, user_id, brand, model, size, price):
        account = await self.get_account(user_id)
        
        if account["balance"] >= price:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cur:
                    # Списуємо кошти
                    await cur.execute(
                        "UPDATE users SET balance=balance-%s, purchases=purchases+1 WHERE user_id=%s", 
                        (price, user_id)
                    )
                    # Записуємо продаж
                    await cur.execute(
                        "INSERT INTO sales (user_id, brand, model, size, price) VALUES (%s, %s, %s, %s, %s)",
                        (user_id, brand, model, size, price)
                    )
            return {"success": True, "final_price": price}
        return {"success": False}

    # Історія покупок
    async def get_purchase_history(self, user_id, limit=10):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT brand, model, size, price, created_at FROM sales WHERE user_id=%s ORDER BY created_at DESC LIMIT %s",
                    (user_id, limit)
                )
                rows = await cur.fetchall()
                return [
                    {
                        "brand": row[0],
                        "model": row[1], 
                        "size": row[2],
                        "price": row[3],
                        "date": row[4]
                    }
                    for row in rows
                ]

    # Отримання списку адміністраторів
    async def get_admins(self):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT user_id FROM users WHERE status='admin'")
                rows = await cur.fetchall()
                return [row[0] for row in rows]

    # Створення заявки на поповнення
    async def create_payment_order(self, user_id, amount, payment_method='card'):
        import random
        import string
        
        # Генеруємо ID замовлення
        order_id = ''.join(random.choices(string.digits, k=10))
        logger.info(f"Створення замовлення на поповнення: {order_id} для користувача {user_id} сума {amount} метод {payment_method}")
        
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT INTO payment_orders (order_id, user_id, amount, payment_method) VALUES (%s, %s, %s, %s)",
                    (order_id, user_id, amount, payment_method)
                )
        
        logger.info(f"Замовлення на поповнення {order_id} успішно створено")
        return order_id

    # Отримання заявки на поповнення
    async def get_payment_order(self, order_id):
        logger.info(f"Отримання замовлення: {order_id}")
        
        # Перевіряємо та видаляємо префікс crypto_ якщо він є
        if isinstance(order_id, str) and order_id.startswith("crypto_"):
            order_id_to_query = order_id[len("crypto_"):]
            logger.info(f"Видалення префіксу 'crypto_', пошук з ID: {order_id_to_query}")
        else:
            order_id_to_query = order_id
        
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT order_id, user_id, amount, status, payment_method FROM payment_orders WHERE order_id=%s",
                    (order_id_to_query,)
                )
                row = await cur.fetchone()
                if row:
                    result = {
                        "order_id": row[0],
                        "user_id": row[1],
                        "amount": row[2],
                        "status": row[3],
                        "payment_method": row[4] if len(row) > 4 else "card"  # Для зворотної сумісності
                    }
                    logger.info(f"Знайдено замовлення: {result}")
                    return result
                else:
                    logger.warning(f"Замовлення {order_id} не знайдено")
                    return None

    # Підтвердження поповнення
    async def approve_payment(self, order_id):
        logger.info(f"Підтвердження замовлення: {order_id}")
        
        order = await self.get_payment_order(order_id)
        if order and order["status"] == "pending":
            try:
                async with self.pool.acquire() as conn:
                    async with conn.cursor() as cur:
                        # Оновлюємо статус
                        await cur.execute(
                            "UPDATE payment_orders SET status='approved' WHERE order_id=%s",
                            (order_id,)
                        )
                        # Зараховуємо кошти
                        await cur.execute(
                            "UPDATE users SET balance=balance+%s WHERE user_id=%s",
                            (order["amount"], order["user_id"])
                        )
                logger.info(f"Замовлення {order_id} успішно підтверджено")
                return True
            except Exception as e:
                logger.error(f"Помилка при підтвердженні замовлення {order_id}: {e}")
                return False
        else:
            logger.warning(f"Не можу підтвердити замовлення {order_id}: order={order}")
            return False

    # Відхилення поповнення
    async def reject_payment(self, order_id):
        logger.info(f"Відхилення замовлення: {order_id}")
        
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE payment_orders SET status='rejected' WHERE order_id=%s",
                    (order_id,)
                )
        
        logger.info(f"Замовлення {order_id} успішно відхилено")

