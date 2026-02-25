# Chapter 9: Fields OnChange

## Overview
Implemented onchange methods to automatically update fields and provide user warnings.

## Exercise 1: Garden OnChange
**Location**: `custom_addons/estate/models/estate_property.py`

Added `_onchange_garden()` method:
- When `garden` is set to `True`: 
  - Sets `garden_area` = 10
  - Sets `garden_orientation` = 'north'
- When `garden` is set to `False`:
  - Clears `garden_area` to 0
  - Clears `garden_orientation` to False

```python
@api.onchange('garden')
def _onchange_garden(self):
    if self.garden:
        self.garden_area = 10
        self.garden_orientation = 'north'
    else:
        self.garden_area = 0
        self.garden_orientation = False
```

## Exercise 2: Date Availability Warning
**Location**: `custom_addons/estate/models/estate_property.py`

Added `_onchange_date_availability()` method:
- Displays a soft warning if `date_availability` is set to a date before today
- Warning message: "The availability date cannot be in the past."

```python
@api.onchange('date_availability')
def _onchange_date_availability(self):
    if self.date_availability and self.date_availability < fields.Date.today():
        return {
            'warning': {
                'title': 'Invalid Date',
                'message': 'The availability date cannot be in the past.',
            }
        }
```

## Key Concepts
- `@api.onchange('field_name')`: Decorator to trigger method when field changes
- Soft warnings: Return dictionary with 'warning' key containing 'title' and 'message'
- OnChange methods update UI in real-time without saving to database

## Testing
1. Create/edit a property and check/uncheck the garden field
2. Try setting an availability date in the past and observe the warning
