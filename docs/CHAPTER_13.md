# Chapter 13: Widgets

## Ringkasan
Chapter ini mengimplementasikan berbagai widget di Odoo untuk meningkatkan user experience pada form dan list view.

## Perubahan yang Dilakukan

### 1. Simple Widgets

#### Statusbar Widget
- **File**: `views/estate_property_views.xml`
- **Implementasi**: Menambahkan widget statusbar pada field `state` di header form view
- **Kode**:
```xml
<field name="state" widget="statusbar" statusbar_visible="new,offer_received,offer_accepted,sold"/>
```
- **Fungsi**: Menampilkan status property dalam bentuk progress bar yang visual dan mudah dipahami

#### Radio Button Widget
- **File**: `views/estate_property_views.xml`
- **Implementasi**: Mengubah field `garden_orientation` menjadi radio button selection
- **Kode**:
```xml
<field name="garden_orientation" widget="radio" invisible="not garden"/>
```
- **Fungsi**: Menampilkan pilihan orientasi taman dalam bentuk radio button

### 2. Advanced Widgets

#### Color Field pada Tags
- **File**: `models/estate_property_tag.py`
- **Implementasi**: Menambahkan field `color` (Integer) pada model `estate.property.tag`
- **Kode**:
```python
color = fields.Integer()
```

#### Many2Many Tags dengan Color Picker
- **File**: `views/estate_property_views.xml`
- **Implementasi**: Menambahkan opsi color_field pada widget many2many_tags
- **Kode**:
```xml
<field name="tag_ids" widget="many2many_tags" options="{'color_field': 'color'}"/>
```
- **Fungsi**: Menampilkan color picker pada tags untuk memberikan warna identitas unik

#### Many2One dengan Pembatasan
- **File**: `views/estate_property_views.xml`
- **Implementasi**: Menambahkan opsi no_create dan no_open pada field `property_type_id`
- **Kode**:
```xml
<field name="property_type_id" options="{'no_create': True, 'no_open': True}"/>
```
- **Fungsi**: 
  - `no_create`: Mencegah pembuatan property type baru langsung dari form property
  - `no_open`: Mencegah pembukaan form property type dari field

## Testing

Jalankan upgrade module untuk menerapkan perubahan:
```bash
.\odoo\odoo-bin -c odoo.conf -u estate
```

## Hasil
- State property ditampilkan sebagai statusbar di header form
- Garden orientation menggunakan radio button untuk pilihan yang lebih jelas
- Tags memiliki color picker untuk personalisasi visual
- Property type dibatasi untuk mencegah pembuatan/editing yang tidak terencana
