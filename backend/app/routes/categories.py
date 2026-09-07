"""Category management routes"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.models import Category
from app.schemas import CategoryCreate, Category as CategorySchema
from app.utils import generate_uuid, get_current_user

router = APIRouter()


@router.post("/", response_model=CategorySchema, status_code=status.HTTP_201_CREATED)
async def create_category(
    cat_data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    if cat_data.parent_id:
        result = await db.execute(
            select(Category).where(
                Category.id == cat_data.parent_id, Category.auth_user_id == current_user.id
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Parent category not found")

    category = Category(
        id=generate_uuid(),
        auth_user_id=current_user.id,
        name=cat_data.name,
        type=cat_data.type,
        parent_id=cat_data.parent_id,
        color=cat_data.color,
        icon=cat_data.icon,
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


@router.get("/", response_model=list[CategorySchema])
async def list_categories(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    result = await db.execute(
        select(Category).where(Category.auth_user_id == current_user.id)
    )
    return result.scalars().all()


@router.get("/{category_id}", response_model=CategorySchema)
async def get_category(
    category_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    result = await db.execute(
        select(Category).where(
            Category.id == category_id, Category.auth_user_id == current_user.id
        )
    )
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.put("/{category_id}", response_model=CategorySchema)
async def update_category(
    category_id: str,
    cat_data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    result = await db.execute(
        select(Category).where(
            Category.id == category_id, Category.auth_user_id == current_user.id
        )
    )
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    update_data = cat_data.model_dump(exclude_unset=True)
    if "parent_id" in update_data and update_data["parent_id"]:
        result = await db.execute(
            select(Category).where(
                Category.id == update_data["parent_id"], Category.auth_user_id == current_user.id
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Parent category not found")

    for field, value in update_data.items():
        setattr(category, field, value)

    await db.commit()
    await db.refresh(category)
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    result = await db.execute(
        select(Category).where(
            Category.id == category_id, Category.auth_user_id == current_user.id
        )
    )
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    await db.delete(category)
    await db.commit()