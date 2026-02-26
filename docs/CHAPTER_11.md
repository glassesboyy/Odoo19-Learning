# Chapter 11: Constraints

## Ringkasan
Implementasi SQL dan Python constraints untuk validasi data pada modul Estate.

## 1. SQL Constraints

SQL constraints divalidasi langsung di level database untuk memastikan integritas data.

### Property - Expected dan Selling Price
**Lokasi**: `custom_addons/estate/models/estate_property.py`

```python
_sql_constraints = [
    ('check_expected_price_positive', 'CHECK(expected_price > 0)', 'Expected price must be strictly positive.'),
    ('check_selling_price_positive', 'CHECK(selling_price >= 0)', 'Selling price must be positive.'),
]
```

- **expected_price**: Harus lebih besar dari 0 (strictly positive)
- **selling_price**: Harus lebih besar atau sama dengan 0 (positive)

### Property Offer - Price
**Lokasi**: `custom_addons/estate/models/estate_property_offer.py`

```python
_sql_constraints = [
    ('check_offer_price_positive', 'CHECK(price > 0)', 'Offer price must be strictly positive.'),
]
```

- **price**: Harus lebih besar dari 0 (strictly positive)

### Property Tag - Unique Name
**Lokasi**: `custom_addons/estate/models/estate_property_tag.py`

```python
_sql_constraints = [
    ('unique_tag_name', 'UNIQUE(name)', 'Tag name must be unique.'),
]
```

- **name**: Setiap tag harus memiliki nama yang unik

### Property Type - Unique Name
**Lokasi**: `custom_addons/estate/models/estate_property_type.py`

```python
_sql_constraints = [
    ('unique_type_name', 'UNIQUE(name)', 'Type name must be unique.'),
]
```

- **name**: Setiap type harus memiliki nama yang unik

## 2. Python Constraints

Python constraints divalidasi di level aplikasi dengan logika yang lebih kompleks.

### Selling Price Validation
**Lokasi**: `custom_addons/estate/models/estate_property.py`

```python
@api.constrains('selling_price', 'expected_price')
def _check_selling_price(self):
    for record in self:
        if record.selling_price > 0 and record.selling_price < (0.9 * record.expected_price):
            raise ValidationError("Selling price cannot be lower than 90% of the expected price.")
```

**Logika**:
- Selling price tidak boleh lebih rendah dari 90% expected price
- **Penting**: Constraint hanya trigger ketika selling_price > 0
  - Ini untuk handle kasus default selling_price = 0 sebelum ada offer yang accepted
- Constraint trigger saat `selling_price` atau `expected_price` berubah

## Konsep Penting

### SQL Constraints
- **Syntax**: `('constraint_name', 'SQL_CONDITION', 'Error message')`
- **Level**: Database
- **Keuntungan**: 
  - Cepat dan efisien
  - Validasi di level database menjamin integritas
- **Tipe**:
  - `CHECK`: Validasi kondisi tertentu
  - `UNIQUE`: Memastikan nilai unique
  - `NOT NULL`: Field tidak boleh null (sudah ada di required=True)

### Python Constraints
- **Decorator**: `@api.constrains('field1', 'field2')`
- **Level**: Aplikasi (Python)
- **Exception**: `ValidationError` dari `odoo.exceptions`
- **Keuntungan**:
  - Logika kompleks yang tidak bisa dilakukan SQL
  - Error message yang lebih dinamis
  - Akses ke relational fields dan computed fields

### Pattern
```python
from odoo.exceptions import ValidationError

@api.constrains('field1', 'field2')
def _check_something(self):
    for record in self:
        if invalid_condition:
            raise ValidationError("Error message")
```

## Testing

### Test SQL Constraints

**Test 1: Expected Price**
1. Buka Estate → Properties → Create
2. Isi nama property
3. **Expected Price**: Isi `0` atau nilai negatif
4. Klik Save → Error: "Expected price must be strictly positive."

**Test 2: Offer Price**
1. Buka sebuah property
2. Tab Offers → Add a line
3. **Price**: Isi `0` atau nilai negatif
4. Save property → Error: "Offer price must be strictly positive."

**Test 3: Unique Tag Name**
1. Buka Estate → Settings → Property Tags
2. Create tag dengan nama "Luxury" (sudah ada di demo data)
3. Save → Error: "Tag name must be unique."

**Test 4: Unique Type Name**
1. Buka Estate → Settings → Property Types
2. Create type dengan nama "House" (sudah ada di demo data)
3. Save → Error: "Type name must be unique."

### Test Python Constraint

**Test: Selling Price vs Expected Price**
1. Buka property dengan expected price `300000`
2. Tambahkan offer dengan price `250000` (83% dari expected)
3. Accept offer tersebut
4. Error muncul: "Selling price cannot be lower than 90% of the expected price."
5. **Valid**: Offer dengan price minimal `270000` (90% dari 300000)

**Test: Selling Price Zero (default) - Tidak Error**
1. Buat property baru
2. Expected Price: `200000`
3. Selling Price: 0 (default)
4. Save → **Tidak ada error** (karena constraint hanya check jika selling_price > 0)

## File yang Dimodifikasi

1. **models/estate_property.py**: 
   - SQL constraints: expected_price dan selling_price
   - Python constraint: _check_selling_price()
   - Import ValidationError
2. **models/estate_property_offer.py**: SQL constraint untuk price
3. **models/estate_property_tag.py**: SQL constraint unique name
4. **models/estate_property_type.py**: SQL constraint unique name

## ⚠️ PENTING: Cara Menerapkan Constraints

SQL constraints **TIDAK otomatis diterapkan** ke tabel database yang sudah ada. Constraints hanya dibuat saat tabel pertama kali dibuat.

### Solusi 1: Uninstall & Reinstall Module (RECOMMENDED)
1. Buka Odoo → Apps
2. Hapus filter "Apps" → Klik filter "Installed"
3. Cari "Estate" → Klik "Uninstall"
4. Konfirmasi uninstall
5. Cari lagi "Estate" → Klik "Install"
6. Semua constraints sekarang sudah aktif di database

**Note**: Data demo akan dibuat ulang, data lama akan hilang.

### Solusi 2: Manual SQL (Jika Ingin Pertahankan Data)

Jalankan SQL berikut di database PostgreSQL:

```sql
-- Property constraints
ALTER TABLE estate_property 
  DROP CONSTRAINT IF EXISTS check_expected_price_positive,
  ADD CONSTRAINT check_expected_price_positive CHECK(expected_price > 0);

ALTER TABLE estate_property 
  DROP CONSTRAINT IF EXISTS check_selling_price_positive,
  ADD CONSTRAINT check_selling_price_positive CHECK(selling_price >= 0);

-- Offer constraint
ALTER TABLE estate_property_offer 
  DROP CONSTRAINT IF EXISTS check_offer_price_positive,
  ADD CONSTRAINT check_offer_price_positive CHECK(price > 0);

-- Tag unique constraint
ALTER TABLE estate_property_tag 
  DROP CONSTRAINT IF EXISTS unique_tag_name,
  ADD CONSTRAINT unique_tag_name UNIQUE(name);

-- Type unique constraint
ALTER TABLE estate_property_type 
  DROP CONSTRAINT IF EXISTS unique_type_name,
  ADD CONSTRAINT unique_type_name UNIQUE(name);
```

### Solusi 3: Hapus Data Invalid, Lalu Restart Odoo

Jika ada data yang melanggar constraint:
1. Hapus data dengan expected_price <= 0
2. Hapus tag/type duplikat
3. Uninstall & Reinstall module

## Troubleshooting

**Error saat install ulang:**
- Jika ada data lama yang melanggar constraint, install akan gagal
- Solusi: Hapus semua data estate via database atau drop semua tabel estate_*

**Constraint tidak trigger setelah reinstall:**
- Pastikan sudah restart Odoo
- Cek di database apakah constraint ada:
  ```sql
  -- Check constraints di PostgreSQL
  SELECT conname, contype, pg_get_constraintdef(oid) 
  FROM pg_constraint 
  WHERE conrelid = 'estate_property'::regclass;
  ```

## Checklist Implementasi
- ✅ SQL constraint: expected_price > 0
- ✅ SQL constraint: selling_price >= 0
- ✅ SQL constraint: offer price > 0
- ✅ SQL constraint: unique tag name
- ✅ SQL constraint: unique type name
- ✅ Python constraint: selling price >= 90% expected price (dengan handling selling_price = 0)
