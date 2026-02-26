# Chapter 14: Ordering

## Ringkasan
Chapter ini mengimplementasikan ordering (pengurutan) pada model untuk menampilkan data dengan urutan yang lebih logis dan user-friendly.

## Perubahan yang Dilakukan

### 1. Model Ordering

Menambahkan atribut `_order` pada setiap model untuk pengurutan otomatis:

#### Estate Property
- **File**: `models/estate_property.py`
- **Order**: Descending ID (terbaru dahulu)
- **Kode**:
```python
_order = 'id desc'
```

#### Estate Property Offer
- **File**: `models/estate_property_offer.py`
- **Order**: Descending Price (harga tertinggi dahulu)
- **Kode**:
```python
_order = 'price desc'
```

#### Estate Property Tag
- **File**: `models/estate_property_tag.py`
- **Order**: Name (alfabetis)
- **Kode**:
```python
_order = 'name'
```

#### Estate Property Type
- **File**: `models/estate_property_type.py`
- **Order**: Sequence, Name
- **Kode**:
```python
_order = 'sequence, name'
```

### 2. Manual Ordering

Menambahkan field `sequence` pada model `estate.property.type` untuk pengurutan manual menggunakan drag-and-drop.

#### Field Sequence
- **File**: `models/estate_property_type.py`
- **Implementasi**:
```python
sequence = fields.Integer(default=10)
```

#### Handle Widget di List View
- **File**: `views/estate_property_type_views.xml`
- **Implementasi**:
```xml
<field name="sequence" widget="handle"/>
```
- **Fungsi**: Memungkinkan drag-and-drop untuk mengubah urutan property type secara manual

## Testing

Jalankan upgrade module untuk menerapkan perubahan:
```bash
.\odoo\odoo-bin -c odoo.conf -u estate
```

## Hasil
- Property ditampilkan dengan ID terbaru di atas
- Offer diurutkan dari harga tertinggi
- Tag diurutkan alfabetis
- Property Type dapat diurutkan manual dengan drag-and-drop
