from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from database import get_db
from database import User, Ticket  # Changed from 'models' to 'database'
from keyboards.user_keyboards import *
from utils.helpers import generate_ticket_id, format_ticket_for_admin
from config import Config
import logging

router = Router()

class TicketForm(StatesGroup):
    choosing_category = State()
    entering_name = State()
    entering_email = State()
    entering_phone = State()
    entering_description = State()

# ... rest of the code remains the same
