from datetime import datetime, timedelta
from libgravatar import Gravatar

import unittest
from unittest.mock import MagicMock, AsyncMock, patch

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import User, Contact
from src.schemas.contact import ContactSchema, ContactUpdateSchema
from src.schemas.user import UserSchema
from src.repository.contacts import (
    get_contacts,
    get_contact,
    get_contact_by_last_name,
    get_contact_by_email,
    get_contact_by_birthday,
    get_birthdays,
    create_contact,
    update_contact,
    delete_contact
)
from src.repository.users import (
    get_user_by_email,
    create_user,
    update_token,
    confirmed_email,
    update_avatar,
    update_password,
)


class TestAsyncContacts(unittest.IsolatedAsyncioTestCase):

    def setUp(self) -> None:
        self.user = User(
            id=1,
            username="test_user",
            email="test_user@example.com",
            password="qwerty",
            avatar=None,
            refresh_token="test_token",
            created_at=datetime.now(), 
            updated_at=datetime.now(),
            confirmed=True,
        )
        self.session = AsyncMock(spec=AsyncSession)
        self.contacts = [
            Contact(
                id=1,
                first_name="test_name_1",
                last_name="test_surname_1",
                email="test_user_1@example.com",
                birthday=datetime.now(),
                additional_data=None,
                user=self.user,
            ),
            Contact(
                id=2,
                first_name="test_name_2",
                last_name="test_surname_2",
                email="test_user_2@example.com",
                birthday=datetime.now(),
                additional_data=None,
                user=self.user,
            ),
        ]

    async def test_get_contacts(self):
        limit = 10
        offset = 0
        mocked_contacts = MagicMock()
        mocked_contacts.scalars.return_value.all.return_value = self.contacts
        self.session.execute.return_value = mocked_contacts
        result = await get_contacts(limit, offset, self.session, self.user)
        self.assertEqual(result, self.contacts)

    async def test_get_contact(self):
        contact_id = 1
        mocked_result = MagicMock()
        mocked_result.scalar_one_or_none.return_value = self.contacts[0]
        self.session.execute.return_value = mocked_result
        result = await get_contact(contact_id, self.session, self.user)
        self.assertEqual(result, self.contacts[0])

    async def test_get_contact_by_email(self):
        contact_email = "test_user_1@example.com"
        mocked_result = MagicMock()
        mocked_result.scalar_one_or_none.return_value = self.contacts[0]
        self.session.execute.return_value = mocked_result
        result = await get_contact_by_email(contact_email, self.session, self.user)
        self.assertEqual(result, self.contacts[0])

    async def test_get_contact_by_last_name(self):
        contact_last_name = "test_surname_2"
        mocked_result = MagicMock()
        mocked_result.scalars.return_value.all.return_value = [self.contacts[1]]
        self.session.execute.return_value = mocked_result
        result = await get_contact_by_last_name(
            contact_last_name, self.session, self.user
        )
        self.assertEqual(result, [self.contacts[1]])

    async def test_get_contact_by_birthday(self):
        contact_birthday = self.contacts[1].birthday
        mocked_result = MagicMock()
        mocked_result.scalars.return_value.all.return_value = [self.contacts[1]]
        self.session.execute.return_value = mocked_result
        result = await get_contact_by_birthday(
            contact_birthday, self.session, self.user
        )
        self.assertEqual(result, [self.contacts[1]])

    async def test_get_birthdays(self):
        current_date = datetime.now()
        contact_birthday_soon = current_date + timedelta(days=5)
        self.contacts.append(
            Contact(
                id=4,
                first_name="test_name_3",
                last_name="test_surname_3",
                email="test_user_3@example.com",
                birthday=contact_birthday_soon,
                additional_data=None,
                user=self.user,
            )
        )
        mocked_result = MagicMock()
        mocked_result.scalars.return_value.all.return_value = [
            self.contacts[0], self.contacts[1]
        ]
        self.session.execute.return_value = mocked_result
        result = await get_birthdays(self.session, self.user)
        self.assertEqual(result, [self.contacts[0], self.contacts[1]])

    async def test_update_contact(self):
        contact_id = 1
        body = ContactUpdateSchema(
            first_name="test_name_updated",
            last_name="test_surname_updated",
            email="test_user_updated@example.com",
            birthday=datetime.now().date(),
            additional_data='',
        )
        mocked_result = MagicMock()
        mocked_result.scalar_one_or_none.return_value = self.contacts[0]
        self.session.execute.return_value = mocked_result
        result = await update_contact(contact_id, body, self.session, self.user)
        self.assertIsInstance(result, Contact)
        self.assertEqual(result.first_name, 'test_name_updated')
        self.assertEqual(result.last_name, 'test_surname_updated')
        self.assertEqual(result.email, 'test_user_updated@example.com')
        self.assertEqual(result.birthday, body.birthday)
        self.assertEqual(result.additional_data, body.additional_data)

    async def test_delete_contact(self):
        contact_id=1
        mocked_result = MagicMock()
        mocked_result.scalar_one_or_none.return_value = self.contacts[0]
        self.session.execute.return_value = mocked_result
        result = await delete_contact(contact_id, self.session, self.user)
        self.session.delete.assert_called_once()
        self.session.commit.assert_called_once()
        self.assertIsInstance(result, Contact)

    async def test_create_contact_already_exists(self):
        body = ContactSchema(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            birthday=datetime.now().date(),
            additional_data="",
        )
        # Mock the session to return an existing contact
        existing_contact_mock = AsyncMock()
        existing_contact_mock.fetchone.return_value = Contact(
            id=1,
            first_name=body.first_name,
            last_name=body.last_name,
            email=body.email,
            birthday=body.birthday,
            additional_data=body.additional_data,
            user=self.user,
        )
        self.session.execute.return_value = existing_contact_mock

        # Call the create_contact function and assert it raises an HTTPException
        with self.assertRaises(HTTPException) as context:
            await create_contact(body, self.session, self.user)

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "Contact is already exist")

    async def asyncTearDown(self):
        await self.session.close()


class TestUserRepository(unittest.IsolatedAsyncioTestCase):

    def setUp(self) -> None:
        self.user = User(
            id=1,
            username="test_user",
            email="test_user@example.com",
            password="qwerty",
            avatar=None,
            refresh_token="test_token",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            confirmed=True,
        )
        self.session = AsyncMock(spec=AsyncSession)

    async def test_get_user_by_email(self):
        email = "test_user@example.com"
        mocked_result = MagicMock()
        mocked_result.scalar_one_or_none.return_value = self.user
        self.session.execute.return_value = mocked_result
        result = await get_user_by_email(email, self.session)
        self.assertEqual(result, self.user)

    async def test_create_user(self):
        body = UserSchema(
            username="new_user",
            email="new_user@example.com",
            password="password_1",
        )
        self.session.add = AsyncMock()
        self.session.commit = AsyncMock()
        self.session.refresh = AsyncMock()
        result = await create_user(body, self.session)
        self.session.add.assert_called_once()
        self.session.commit.assert_called_once()
        self.session.refresh.assert_called_once()
        self.assertIsInstance(result, User)
        self.assertEqual(result.username, body.username)
        self.assertEqual(result.email, body.email)

    @patch.object(Gravatar, 'get_image', side_effect=Exception("Gravatar error"))
    async def test_create_user_avatar_exception(self, mock_get_image):
        body = UserSchema(
            username="new_user",
            email="test_user@example.com",
            password="password",
        )

        self.session.add = AsyncMock()
        self.session.commit = AsyncMock()
        self.session.refresh = AsyncMock()

        with self.assertRaises(HTTPException) as context:
            await create_user(body, self.session)

        self.assertEqual(context.exception.status_code, 500)

    async def test_update_token(self):
        new_token = "new_refresh_token"
        await update_token(self.user, new_token, self.session)
        self.assertEqual(self.user.refresh_token, new_token)
        self.session.commit.assert_called_once()

    async def test_confirmed_email(self):
        email = "test_user@example.com"
        mocked_result = MagicMock()
        mocked_result.scalar_one_or_none.return_value = self.user
        self.session.execute.return_value = mocked_result
        await confirmed_email(email, self.session)
        self.assertTrue(self.user.confirmed)
        self.session.commit.assert_called_once()
        self.session.refresh.assert_called_once()

    async def test_update_avatar(self):
        email = "test_user@example.com"
        new_avatar_url = "http://example.com/avatar.png"
        mocked_result = MagicMock()
        mocked_result.scalar_one_or_none.return_value = self.user
        self.session.execute.return_value = mocked_result
        result = await update_avatar(email, new_avatar_url, self.session)
        self.assertEqual(result.avatar, new_avatar_url)
        self.session.commit.assert_called_once()

    async def test_update_password(self):
        new_password = "password"
        await update_password(self.user, new_password, self.session)
        self.assertEqual(self.user.password, new_password)
        # self.session.commit.assert_called_once()
        # self.session.refresh.assert_called_once()

    async def asyncTearDown(self):
        await self.session.close()
