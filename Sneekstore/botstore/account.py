import logging
from aiogram import F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

logger = logging.getLogger(__name__)

# Стани для введення сум
class PaymentStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_crypto_amount = State()

# Тимчасові дані про платежі
pending_payments = {}

# Клавіатура аккаунту
def get_account_menu():
    kb = [
        [InlineKeyboardButton(text="Поповнити баланс", callback_data="topup_balance")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# Клавіатура вибору способу поповнення
def get_topup_menu():
    kb = [
        [
            InlineKeyboardButton(text="Поповнити криптовалютою", callback_data="topup_crypto"),
            InlineKeyboardButton(text="Поповнити картою", callback_data="topup_card")
        ],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="account")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# Реєстрація всіх обробників аккаунту
def register_account_handlers(dp, db, bot):
    
    # Показ інформації про аккаунт
    @dp.callback_query(F.data == "account")
    async def process_account(callback_query):
        user_id = callback_query.from_user.id
        user_name = callback_query.from_user.first_name or callback_query.from_user.username or "Невідомий користувач"
        logger.info(f"Користувач {user_name} (ID: {user_id}) натиснув 'Аккаунт'")
        
        # Отримуємо дані з бази даних
        account = await db.get_account(user_id)
        balance = account["balance"]
        purchases = account["purchases"]
        
        try:
            await callback_query.message.delete()
        except Exception:
            pass
        await callback_query.message.answer(
            f"👤 <b>Ваш аккаунт</b>\n\n"
            f"Ім'я: <b>{user_name}</b>\n"
            f"Баланс: <b>{balance} грн</b>\n"
            f"Кількість покупок: <b>{purchases}</b>",
            parse_mode="HTML",
            reply_markup=get_account_menu()
        )

    # Вибір способу поповнення балансу
    @dp.callback_query(F.data == "topup_balance")
    async def process_topup_balance(callback_query):
        await callback_query.answer()
        try:
            await callback_query.message.delete()
        except Exception:
            pass
        await callback_query.message.answer(
            "💳 <b>Оберіть спосіб поповнення балансу:</b>",
            parse_mode="HTML",
            reply_markup=get_topup_menu()
        )

    # Поповнення картою - запит суми
    @dp.callback_query(F.data == "topup_card")
    async def process_topup_card(callback_query, state: FSMContext):
        await callback_query.answer()
        try:
            await callback_query.message.delete()
        except Exception:
            pass
        await callback_query.message.answer(
            "💳 <b>Поповнення картою</b>\n"
            "\n"
            "Введіть суму для поповнення балансу (у гривнях):\n"
            "\n"
            "<i>Приклад: 500</i>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="topup_balance")]
            ])
        )
        await state.set_state(PaymentStates.waiting_for_amount)

    # Поповнення криптовалютою - запит суми
    @dp.callback_query(F.data == "topup_crypto")
    async def process_topup_crypto(callback_query, state: FSMContext):
        await callback_query.answer()
        try:
            await callback_query.message.delete()
        except Exception:
            pass
        await callback_query.message.answer(
            "🪙 <b>Поповнення криптовалютою</b>\n"
            "\n"
            "Введіть суму для поповнення балансу (у гривнях):\n"
            "\n"
            "<i>Приклад: 500</i>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="topup_balance")]
            ])
        )
        await state.set_state(PaymentStates.waiting_for_crypto_amount)

    # Обробка суми для поповнення картою
    @dp.message(PaymentStates.waiting_for_amount)
    async def process_payment_amount(message: Message, state: FSMContext):
        try:
            amount = float(message.text)
            if amount <= 0:
                await message.answer("❌ Сума повинна бути більше 0!")
                return
                
            user_id = message.from_user.id
            
            # Створюємо заявку з вказанням методу оплати
            order_id = await db.create_payment_order(user_id, amount, payment_method='card')
            
            # Зберігаємо дані
            pending_payments[order_id] = {
                "user_id": user_id,
                "amount": amount,
                "username": message.from_user.first_name or message.from_user.username or "Невідомий"
            }
            
            # Інформація для оплати картою
            payment_info = (
                f"💳 <b>Інформація для оплати</b>\n"
                f"\n"
                f"📋 Номер замовлення: <code>№{order_id}</code>\n"
                f"💰 Сума: <b>{amount:.0f} грн</b>\n"
                f"\n"
                f"💳 <b>Реквізити для оплати:</b>\n"
                f"Картка: <code>4444 4444 4444 4444</code>\n"
                f"Отримувач: Іванов Іван Іванович\n"
                f"Банк: ПриватБанк\n"
                f"\n"
                f"❗️ <b>Важливо:</b>\n"
                f"• Вкажіть номер замовлення в коментарі\n"
                f"• Сума має точно відповідати зазначеній\n"
                f"• Після оплати натисніть кнопку нижче"
            )
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Я оплатив", callback_data=f"paid_{order_id}")],
                [InlineKeyboardButton(text="❌ Скасувати", callback_data="topup_balance")]
            ])
            
            await message.answer(payment_info, parse_mode="HTML", reply_markup=keyboard)
            await state.clear()
            
        except ValueError:
            await message.answer("❌ Введіть коректну суму числом!")

    # Обробка суми для поповнення криптовалютою
    @dp.message(PaymentStates.waiting_for_crypto_amount)
    async def process_crypto_payment_amount(message: Message, state: FSMContext):
        try:
            amount = float(message.text)
            if amount <= 0:
                await message.answer("❌ Сума повинна бути більше 0!")
                return
                
            user_id = message.from_user.id
            
            # Створюємо заявку в базі даних з вказанням методу оплати
            order_id = await db.create_payment_order(user_id, amount, payment_method='crypto')
            
            # Зберігаємо дані в пам'яті
            pending_payments[order_id] = {
                "user_id": user_id,
                "amount": amount,
                "username": message.from_user.first_name or message.from_user.username or "Невідомий",
                "payment_type": "crypto"
            }
            
            # Конвертація в USDT
            usd_amount = amount / 41
            
            # Інформація для криптоплатежу
            payment_info = (
                f"🪙 <b>Інформація для оплати криптовалютою</b>\n"
                f"\n"
                f"📋 Номер замовлення: <code>№{order_id}</code>\n"
                f"💰 Сума: <b>{amount:.0f} грн</b>\n"
                f"💵 Сума в USDT: <b>{usd_amount:.2f} USDT</b>\n"
                f"\n"
                f"🪙 <b>Реквізити для оплати:</b>\n"
                f"Мережа: <code>TRC20 (Tron)</code>\n"
                f"Адреса: <code>TQRKqHvdqwdGTELjFUzYzVqhxMtaworR3a</code>\n"
                f"Валюта: <code>USDT</code>\n"
                f"\n"
                f"❗️ <b>Важливо:</b>\n"
                f"• Відправляйте тільки USDT по мережі TRC20\n"
                f"• Сума має точно відповідати зазначеній в USDT\n"
                f"• Після відправки натисніть кнопку нижче\n"
                f"• Вкажіть номер замовлення в коментарі"
            )
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Я відправив", callback_data=f"crypto_paid_{order_id}")],
                [InlineKeyboardButton(text="❌ Скасувати", callback_data="topup_balance")]
            ])
            
            await message.answer(payment_info, parse_mode="HTML", reply_markup=keyboard)
            await state.clear()
            
        except ValueError:
            await message.answer("❌ Введіть коректну суму числом!")

    # Підтвердження оплати картою
    @dp.callback_query(F.data.startswith("paid_"))
    async def process_payment_confirmation(callback_query):
        order_id = callback_query.data.split("_", 1)[1]
        user_id = callback_query.from_user.id
        
        # Перевіряємо заявку
        order = await db.get_payment_order(order_id)
        if not order or order["user_id"] != user_id:
            await callback_query.answer("❌ Заявка не знайдена!")
            return
        
        if order["status"] != "pending":
            await callback_query.answer("❌ Заявка вже оброблена!")
            return
        
        await callback_query.answer("✅ Заявка отримана!")
        await callback_query.message.edit_text(
            f"✅ <b>Заявка на поповнення отримана!</b>\n"
            f"\n"
            f"📋 Номер замовлення: <code>№{order_id}</code>\n"
            f"💰 Сума: <b>{order['amount']:.0f} грн</b>\n"
            f"\n"
            f"⏳ Ваша заявка передана на розгляд адміністратору.\n"
            f"Зазвичай обробка займає до 30 хвилин.\n"
            f"📱 Ви отримаєте повідомлення про зарахування коштів.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏠 Головне меню", callback_data="back_to_main")]
            ])
        )
        
        # Повідомляємо адміністраторів
        admins = await db.get_admins()
        user_info = pending_payments.get(order_id, {})
        username = user_info.get("username", "Невідомий")
        
        admin_message = (
            f"💳 <b>Нова заявка на поповнення картою!</b>\n"
            f"\n"
            f"👤 Користувач: {username}\n"
            f"🆔 ID: <code>{user_id}</code>\n"
            f"📋 Номер замовлення: <code>№{order_id}</code>\n"
            f"💰 Сума: <b>{order['amount']:.0f} грн</b>\n"
            f"\n"
            f"Перевірте оплату та підтвердьте або відхиліть заявку:"
        )
        
        admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Підтвердити", callback_data=f"approve_{order_id}"),
                InlineKeyboardButton(text="❌ Відхилити", callback_data=f"reject_{order_id}")
            ]
        ])
        
        for admin_id in admins:
            try:
                await bot.send_message(admin_id, admin_message, parse_mode="HTML", reply_markup=admin_keyboard)
            except Exception as e:
                logger.error(f"Не вдалося відправити повідомлення адміну {admin_id}: {e}")

    # Підтвердження адміном платежу картою
    @dp.callback_query(F.data.startswith("approve_"))
    async def approve_payment(callback_query):
        order_id = callback_query.data.split("_", 1)[1]
        
        success = await db.approve_payment(order_id)
        if success:
            order = await db.get_payment_order(order_id)
            if order:
                payment_type = "карткою" if order.get('payment_method') == 'card' else "криптовалютою"
                await callback_query.answer("✅ Платіж підтверджено!")
                await callback_query.message.edit_text(
                    f"✅ <b>Платіж {payment_type} підтверджено!</b>\n"
                    f"\n"
                    f"📋 Замовлення: <code>№{order_id}</code>\n"
                    f"💰 Сума: <b>{order['amount']:.0f} грн</b>\n"
                    f"👤 Користувач: <code>{order['user_id']}</code>\n"
                    f"\n"
                    f"Кошти зараховано на баланс користувача.",
                    parse_mode="HTML"
                )
                
                # Повідомляємо користувача
                try:
                    await bot.send_message(
                        order["user_id"],
                        f"🎉 <b>Баланс поповнено!</b>\n"
                        f"\n"
                        f"📋 Номер замовлення: <code>№{order_id}</code>\n"
                        f"💰 Зарахована сума: <b>{order['amount']:.0f} грн</b>\n"
                        f"💳 Спосіб оплати: {payment_type}\n"
                        f"\n"
                        f"Дякуємо за поповнення! Кошти доступні для покупок.",
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logger.error(f"Не вдалося повідомити користувача {order['user_id']}: {e}")
            else:
                await callback_query.answer("❌ Заявка не знайдена!")
        else:
            await callback_query.answer("❌ Заявка не знайдена або вже оброблена!")

    # Відхилення адміном платежу картою
    @dp.callback_query(F.data.startswith("reject_"))
    async def reject_payment(callback_query):
        order_id = callback_query.data.split("_", 1)[1]
        
        await db.reject_payment(order_id)
        order = await db.get_payment_order(order_id)
        
        if order:
            payment_type = "карткою" if order.get('payment_method') == 'card' else "криптовалютою"
            await callback_query.answer("❌ Платіж відхилено!")
            await callback_query.message.edit_text(
                f"❌ <b>Платіж {payment_type} відхилено!</b>\n"
                f"\n"
                f"📋 Замовлення: <code>№{order_id}</code>\n"
                f"💰 Сума: <b>{order['amount']:.0f} грн</b>\n"
                f"👤 Користувач: <code>{order['user_id']}</code>\n"
                f"\n"
                f"Причина: не підтверджена оплата або інша помилка.",
                parse_mode="HTML"
            )
            
            # Повідомляємо користувача
            try:
                await bot.send_message(
                    order["user_id"],
                    f"❌ <b>Заявка на поповнення {payment_type} відхилена</b>\n"
                    f"\n"
                    f"📋 Номер замовлення: <code>№{order_id}</code>\n"
                    f"💰 Сума: <b>{order['amount']:.0f} грн</b>\n"
                    f"\n"
                    f"Можливі причини:\n"
                    f"• Оплата не надійшла\n"
                    f"• Неправильна сума\n"
                    f"• Відсутній коментар з номером замовлення\n"
                    f"Зверніться до підтримки: @vktrysn",
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Не вдалося повідомити користувача {order['user_id']}: {e}")
        else:
            await callback_query.answer("❌ Заявка не знайдена!")

    # Підтвердження оплати криптовалютою
    @dp.callback_query(F.data.startswith("crypto_paid_"))
    async def process_crypto_payment_confirmation(callback_query):
        order_id = callback_query.data.split("_", 2)[2]
        user_id = callback_query.from_user.id
        
        # Перевіряємо заявку
        order = await db.get_payment_order(order_id)
        if not order or order["user_id"] != user_id:
            await callback_query.answer("❌ Заявка не знайдена!")
            return
        
        if order["status"] != "pending":
            await callback_query.answer("❌ Заявка вже оброблена!")
            return
        
        await callback_query.answer("✅ Заявка отримана!")
        await callback_query.message.edit_text(
            f"✅ <b>Заявка на поповнення криптовалютою отримана!</b>\n"
            f"\n"
            f"📋 Номер замовлення: <code>№{order_id}</code>\n"
            f"💰 Сума: <b>{order['amount']:.0f} грн</b>\n"
            f"\n"
            f"⏳ Ваша заявка передана на розгляд адміністратору.\n"
            f"Зазвичай обробка займає до 60 хвилин.\n"
            f"📱 Ви отримаєте повідомлення про зарахування коштів.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏠 Головне меню", callback_data="back_to_main")]
            ])
        )
        
        # Повідомляємо адміністраторів
        admins = await db.get_admins()
        user_info = pending_payments.get(order_id, {})
        username = user_info.get("username", "Невідомий")
        usd_amount = float(order['amount']) / 41
        
        admin_message = (
            f"🪙 <b>Нова заявка на поповнення криптовалютою!</b>\n"
            f"\n"
            f"👤 Користувач: {username}\n"
            f"🆔 ID: <code>{user_id}</code>\n"
            f"📋 Номер замовлення: <code>№{order_id}</code>\n"
            f"💰 Сума: <b>{order['amount']:.0f} грн</b>\n"
            f"💵 Сума в USDT: <b>{usd_amount:.2f} USDT</b>\n"
            f"🪙 Мережа: TRC20 (Tron)\n"
            f"\n"
            f"Перевірте надходження USDT та підтвердьте або відхиліть заявку:"
        )
        
        admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Підтвердити", callback_data=f"approve_crypto_{order_id}"),
                InlineKeyboardButton(text="❌ Відхилити", callback_data=f"reject_crypto_{order_id}")
            ]
        ])
        
        for admin_id in admins:
            try:
                await bot.send_message(admin_id, admin_message, parse_mode="HTML", reply_markup=admin_keyboard)
            except Exception as e:
                logger.error(f"Не вдалося відправити повідомлення адміну {admin_id}: {e}")

    # Підтвердження адміном криптоплатежу
    @dp.callback_query(F.data.startswith("approve_crypto_"))
    async def approve_crypto_payment(callback_query):
        full_order_id = callback_query.data[len("approve_crypto_"):]
        
        # Перевірка, чи містить order_id префікс "crypto_"
        if full_order_id.startswith("crypto_"):
            order_id = full_order_id[len("crypto_"):]
        else:
            order_id = full_order_id
            
        logger.info(f"Адмін {callback_query.from_user.id} намагається підтвердити крипто-замовлення: {order_id}, повний ID: {full_order_id}")

        # Перевіряємо існування заявки
        order = await db.get_payment_order(order_id)
        logger.info(f"Знайдено замовлення: {order}")
        
        if not order:
            await callback_query.answer("❌ Заявка не знайдена в базі даних!")
            return
            
        if order["status"] != "pending":
            await callback_query.answer(f"❌ Заявка вже оброблена! Статус: {order['status']}")
            return

        success = await db.approve_payment(order_id)
        if success:
            order = await db.get_payment_order(order_id)
            if order:
                usd_amount = float(order['amount']) / 41
                await callback_query.answer("✅ Криптоплатіж підтверджено!")
                await callback_query.message.edit_text(
                    f"✅ <b>Криптоплатіж підтверджено!</b>\n"
                    f"\n"
                    f"📋 Замовлення: <code>№{order_id}</code>\n"
                    f"💰 Сума: <b>{order['amount']:.0f} грн</b>\n"
                    f"💵 USDT: <b>{usd_amount:.2f} USDT</b>\n"
                    f"👤 Користувач: <code>{order['user_id']}</code>\n"
                    f"\n"
                    f"Кошти зараховано на баланс користувача.",
                    parse_mode="HTML"
                )
                try:
                    await bot.send_message(
                        order["user_id"],
                        f"🎉 <b>Баланс поповнено!</b>\n"
                        f"\n"
                        f"📋 Номер замовлення: <code>№{order_id}</code>\n"
                        f"💰 Зарахована сума: <b>{order['amount']:.0f} грн</b>\n"
                        f"\n"
                        f"Дякуємо за поповнення! Кошти доступні для покупок.",
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logger.error(f"Не вдалося повідомити користувача {order['user_id']}: {e}")
            else:
                await callback_query.answer("❌ Заявка не знайдена після обробки!")
        else:
            await callback_query.answer("❌ Помилка при обробці заявки!")

    # Відхилення адміном криптоплатежу
    @dp.callback_query(F.data.startswith("reject_crypto_"))
    async def reject_crypto_payment(callback_query):
        full_order_id = callback_query.data[len("reject_crypto_"):]
        
        # Перевірка, чи містить order_id префікс "crypto_"
        if full_order_id.startswith("crypto_"):
            order_id = full_order_id[len("crypto_"):]
        else:
            order_id = full_order_id
            
        logger.info(f"Адмін {callback_query.from_user.id} намагається відхилити крипто-замовлення: {order_id}, повний ID: {full_order_id}")
        
        # Перевіряємо існування заявки
        order = await db.get_payment_order(order_id)
        logger.info(f"Знайдено замовлення: {order}")
        
        if not order:
            await callback_query.answer("❌ Заявка не знайдена в базі даних!")
            return
            
        if order["status"] != "pending":
            await callback_query.answer(f"❌ Заявка вже оброблена! Статус: {order['status']}")
            return
        
        await db.reject_payment(order_id)
        order = await db.get_payment_order(order_id)
        
        if order:
            usd_amount = float(order['amount']) / 41
            await callback_query.answer("❌ Криптоплатіж відхилено!")
            await callback_query.message.edit_text(
                f"❌ <b>Криптоплатіж відхилено!</b>\n"
                f"\n"
                f"📋 Замовлення: <code>№{order_id}</code>\n"
                f"💰 Сума: <b>{order['amount']:.0f} грн</b>\n"
                f"💵 USDT: <b>{usd_amount:.2f} USDT</b>\n"
                f"👤 Користувач: <code>{order['user_id']}</code>\n"
                f"\n"
                f"Причина: не підтверджене надходження USDT або інша помилка.",
                parse_mode="HTML"
            )
            try:
                await bot.send_message(
                    order["user_id"],
                    f"❌ <b>Заявка на поповнення відхилена</b>\n"
                    f"\n"
                    f"📋 Номер замовлення: <code>№{order_id}</code>\n"
                    f"💰 Сума: <b>{order['amount']:.0f} грн</b>\n"
                    f"\n"
                    f"Можливі причини:\n"
                    f"• Оплата не надійшла\n"
                    f"• Неправильна сума\n"
                    f"• Відсутній коментар з номером замовлення\n"
                    f"Зверніться до підтримки: @vktrysn",
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Не вдалося повідомити користувача {order['user_id']}: {e}")
        else:
            await callback_query.answer("❌ Заявка не знайдена після обробки!")
