# Chapter 9: Fields OnChange

## Ringkasan
Implementasi onchange methods untuk update field otomatis dan menampilkan warning ke user.

## Exercise 1: Garden OnChange
**Lokasi**: `custom_addons/estate/models/estate_property.py`

Method `_onchange_garden()`:
- Ketika `garden` di-check (True): 
  - Set `garden_area` = 10
  - Set `garden_orientation` = 'north'
- Ketika `garden` di-uncheck (False):
  - Kosongkan `garden_area` menjadi 0
  - Kosongkan `garden_orientation` menjadi False

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
**Lokasi**: `custom_addons/estate/models/estate_property.py`

Method `_onchange_date_availability()`:
- Menampilkan soft warning jika `date_availability` diisi dengan tanggal sebelum hari ini
- Pesan warning: "The availability date cannot be in the past."

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

## Konsep Penting
- `@api.onchange('field_name')`: Decorator untuk trigger method ketika field berubah
- Soft warnings: Return dictionary dengan key 'warning' berisi 'title' dan 'message'
- OnChange methods update UI real-time tanpa menyimpan ke database

## Testing
1. Buat/edit property dan check/uncheck field garden
2. Coba set availability date dengan tanggal di masa lalu dan lihat warning-nya
