from fastapi import HTTPException, status
from sqlalchemy import Date, select
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import and_

from src.entity.models import Contact, User
from src.schemas.contact import ContactSchema, ContactUpdateSchema


async def get_contacts(limit: int, offset: int, db: AsyncSession, user: User):
    """
    Retrieves a list of contacts for the specified user within the specified limit and offset.

    Args:
    - limit (int): The maximum number of contacts to retrieve.
    - offset (int): The index from which to start retrieving contacts.
    - db (AsyncSession): The database session.
    - user (User): The user for whom the contacts are being retrieved.

    Returns:
    - list: A list of Contact objects for the specified user within the specified limit and offset.
    """
    stmt = select(Contact).filter_by(user=user).offset(offset).limit(limit)
    result = await db.execute(stmt)
    contacts = result.scalars().all()
    return contacts


async def get_contact(contact_id: int, db: AsyncSession, user: User):
    """
    Retrieves a specific contact by its id for the specified user.

    Args:
    - contact_id (int): The id of the contact to retrieve.
    - db (AsyncSession): The database session.
    - user (User): The user for whom the contact is being retrieved.

    Returns:
    - Contact or None: The specific contact object for the specified user and contact_id, or None if not found.
    """
    stmt = select(Contact).filter_by(id=contact_id, user=user)
    result = await db.execute(stmt)
    contact = result.scalar_one_or_none()
    return contact



async def create_contact(body: ContactSchema, db: AsyncSession, user: User):
    """
    Creates a new contact for the specified user.

    Args:
    - body (ContactSchema): The schema containing the details of the new contact.
    - db (AsyncSession): The database session.
    - user (User): The user for whom the contact is being created.

    Raises:
    - HTTPException: If a contact with the same first name, last name, and email already exists.

    Returns:
    - Contact: The newly created contact object.
    """
    # Перевірка наявності контакту в базі по імені, призвіщу
    existing_contact = await db.execute(
        select(Contact).filter_by(
            first_name=body.first_name, 
            last_name=body.last_name,
            email=body.email
            )
    )
    existing_contact = existing_contact.fetchone()
    if existing_contact:
        raise HTTPException(
            status_code=400,
            detail="Contact is already exist",
        )
    contact = Contact(**body.model_dump(), user=user)
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact

async def delete_contact(contact_id: int, db: AsyncSession, user: User):
    """
    Deletes a specific contact by its id for the specified user.

    Args:
    - contact_id (int): The id of the contact to delete.
    - db (AsyncSession): The database session.
    - user (User): The user for whom the contact is being deleted.

    Returns:
    - Contact or None: The specific contact object for the specified user and contact_id, or None if not found.
    """
    stmt = select(Contact).filter_by(id=contact_id, user=user)
    result = await db.execute(stmt)
    contact = result.scalar_one_or_none()
    if contact:
        await db.delete(contact)
        await db.commit()
    return contact


async def update_contact(
    contact_id: int,  # The id of the contact to update.
    body: ContactUpdateSchema,  # The schema containing the details of the updated contact.
    db: AsyncSession,  # The database session.
    user: User,  # The user for whom the contact is being updated.
) -> Contact:  # Returns the updated contact object.
    """
    Updates a specific contact by its id for the specified user.

    Args:
    - contact_id (int): The id of the contact to update.
    - body (ContactUpdateSchema): The schema containing the details of the updated contact.
    - db (AsyncSession): The database session.
    - user (User): The user for whom the contact is being updated.

    Returns:
    - Contact: The updated contact object.
    """
    stmt = select(Contact).filter_by(id=contact_id, user=user)
    result = await db.execute(stmt)
    contact = result.scalar_one_or_none()
    if contact is None:
        return None
    for key, value in body.model_dump().items():
        setattr(contact, key, value)
    await db.commit()
    await db.refresh(contact)
    return contact


async def get_contact_by_email(contact_email: str, db: AsyncSession, user: User):
    """
    Retrieves a specific contact by its email for the specified user.

    Args:
    - contact_email (str): The email of the contact to retrieve.
    - db (AsyncSession): The database session.
    - user (User): The user for whom the contact is being retrieved.

    Returns:
    - Contact or None: The specific contact object for the specified user and contact_email, or None if not found.
    """
    stmt = select(Contact).filter_by(email=contact_email, user=user)
    result = await db.execute(stmt)
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact is not found",
        )
    return contact


async def get_contact_by_last_name(
    contact_last_name: str,  # The last name of the contact to retrieve.
    db: AsyncSession,  # The database session.
    user: User,  # The user for whom the contact is being retrieved.
) -> list:  # Returns a list of Contact objects for the specified user and last name.
    """
    Retrieves a list of contacts for the specified user with the given last name.

    Args:
    - contact_last_name (str): The last name of the contact to retrieve.
    - db (AsyncSession): The database session.
    - user (User): The user for whom the contact is being retrieved.

    Returns:
    - list: A list of Contact objects for the specified user and last name.
    """
    stmt = select(Contact).filter_by(last_name=contact_last_name, user=user)
    result = await db.execute(stmt)
    contacts = result.scalars().all()
    if not contacts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contacts not found",
        )
    return contacts


async def get_contact_by_birthday(contact_birthday: Date, db: AsyncSession, user: User):
    """
    Retrieves a list of contacts for the specified user with the given birthday.

    Args:
    - contact_birthday (Date): The birthday of the contact to retrieve.
    - db (AsyncSession): The database session.
    - user (User): The user for whom the contact is being retrieved.

    Returns:
    - list: A list of Contact objects for the specified user and birthday.

    Raises:
    - HTTPException: If no contacts are found with the given birthday and user.
    """
    stmt = select(Contact).filter_by(birthday=contact_birthday, user=user)
    result = await db.execute(stmt)
    contacts = result.scalars().all()
    if not contacts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contacts not found",
        )
    return contacts


async def get_birthdays(db: AsyncSession, user: User):
    """
    Retrieves a list of contacts for the specified user with birthdays within the next 7 days.

    Args:
    - db (AsyncSession): The database session.
    - user (User): The user for whom the contacts are being retrieved.

    Returns:
    - list: A list of Contact objects for the specified user with birthdays within the next 7 days.

    Raises:
    - HTTPException: If no contacts are found with the given birthday and user.
    """
    from datetime import datetime, timedelta
    from sqlalchemy import select, and_
    current_date = datetime.now()
    end_date = current_date + timedelta(days=7)
    stmt = select(Contact).filter(
        and_(
            Contact.birthday.between(current_date.date(), end_date.date()),
            Contact.user_id
            == user.id,  # Фільтруємо за ідентифікатором поточного користувача
        )
    )

    result = await db.execute(stmt)
    contacts = result.scalars().all()
    return contacts
