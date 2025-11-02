"""
Input validation utilities
Provides validation functions for user inputs and data sanitization.
"""
import re
from typing import Dict, Any, Optional

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

def validate_category_data(data: Dict[str, Any], update: bool = False) -> Dict[str, Any]:
    """
    Validate category data
    Args:
        data: Raw category data
        update: Whether this is an update operation (allows partial data)
    Returns:
        Validated and sanitized data
    Raises:
        ValidationError: If validation fails
    """
    validated = {}

    # Name validation (required for create, optional for update)
    if 'name' in data or not update:
        name = data.get('name')
        if not name:
            raise ValidationError('Name is required')

        name = str(name).strip()
        if not name:
            raise ValidationError('Name cannot be empty')

        if len(name) > 100:
            raise ValidationError('Name cannot be longer than 100 characters')

        # Check for valid characters (alphanumeric, spaces, hyphens, underscores)
        if not re.match(r'^[a-zA-Z0-9\s\-_]+$', name):
            raise ValidationError('Name contains invalid characters')

        validated['name'] = name

    # Description validation (optional)
    if 'description' in data:
        description = data.get('description')
        if description is not None:
            description = str(description).strip()
            if len(description) > 500:
                raise ValidationError('Description cannot be longer than 500 characters')
            validated['description'] = description

    return validated

def validate_stock_data(data: Dict[str, Any], update: bool = False) -> Dict[str, Any]:
    """
    Validate stock data
    Args:
        data: Raw stock data
        update: Whether this is an update operation (allows partial data)
    Returns:
        Validated and sanitized data
    Raises:
        ValidationError: If validation fails
    """
    validated = {}

    # Name validation (required for create, optional for update)
    if 'name' in data or not update:
        name = data.get('name')
        if not name:
            raise ValidationError('Name is required')

        name = str(name).strip()
        if not name:
            raise ValidationError('Name cannot be empty')

        if len(name) > 200:
            raise ValidationError('Name cannot be longer than 200 characters')

        validated['name'] = name

    # Category ID validation (required for create, optional for update)
    if 'category_id' in data or not update:
        category_id = data.get('category_id')
        if category_id is None:
            raise ValidationError('Category is required')

        try:
            category_id = int(category_id)
            if category_id <= 0:
                raise ValidationError('Invalid category ID')
            validated['category_id'] = category_id
        except (ValueError, TypeError):
            raise ValidationError('Category ID must be a valid number')

    # Quantity validation
    if 'quantity' in data:
        quantity = data.get('quantity')
        try:
            quantity = int(quantity)
            if quantity < 0:
                raise ValidationError('Quantity cannot be negative')
            if quantity > 999999:
                raise ValidationError('Quantity cannot be greater than 999,999')
            validated['quantity'] = quantity
        except (ValueError, TypeError):
            raise ValidationError('Quantity must be a valid number')

    # Unit validation
    if 'unit' in data:
        unit = data.get('unit')
        if unit is not None:
            unit = str(unit).strip()
            if len(unit) > 20:
                raise ValidationError('Unit cannot be longer than 20 characters')

            # Allow common unit formats
            if not re.match(r'^[a-zA-Z0-9/\-\s]*$', unit):
                raise ValidationError('Unit contains invalid characters')

            validated['unit'] = unit or 'pcs'

    # Location validation (optional)
    if 'location' in data:
        location = data.get('location')
        if location is not None:
            location = str(location).strip()
            if len(location) > 100:
                raise ValidationError('Location cannot be longer than 100 characters')
            validated['location'] = location

    # Description validation (optional)
    if 'description' in data:
        description = data.get('description')
        if description is not None:
            description = str(description).strip()
            if len(description) > 1000:
                raise ValidationError('Description cannot be longer than 1000 characters')
            validated['description'] = description

    return validated

def validate_conversation_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate conversation data"""
    validated = {}

    # Title validation
    title = data.get('title')
    if not title:
        raise ValidationError('Title is required')

    title = str(title).strip()
    if not title:
        raise ValidationError('Title cannot be empty')

    if len(title) > 200:
        raise ValidationError('Title cannot be longer than 200 characters')

    validated['title'] = title

    return validated

def validate_message_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate chat message data"""
    validated = {}

    # Role validation
    role = data.get('role')
    if not role:
        raise ValidationError('Role is required')

    if role not in ['user', 'assistant']:
        raise ValidationError('Invalid role')

    validated['role'] = role

    # Message validation
    message = data.get('message')
    if message is None:
        raise ValidationError('Message is required')

    message = str(message).strip()
    if not message:
        raise ValidationError('Message cannot be empty')

    # Reasonable message length limit
    if len(message) > 50000:
        raise ValidationError('Message is too long (max 50,000 characters)')

    validated['message'] = message

    return validated

def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
    """Sanitize string input"""
    if not isinstance(value, str):
        value = str(value)

    # Remove null bytes and other control characters
    value = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', value)

    # Trim whitespace
    value = value.strip()

    # Apply length limit if specified
    if max_length and len(value) > max_length:
        value = value[:max_length]

    return value
