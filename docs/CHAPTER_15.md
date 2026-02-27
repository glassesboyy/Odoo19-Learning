# Chapter 15: Advanced Views

## Ringkasan
Chapter ini mengimplementasikan atribut-atribut advanced pada view untuk meningkatkan user experience dan business logic.

## Perubahan yang Dilakukan

### 1. Attributes - Conditional Display

#### Invisible pada Button
- **File**: `views/estate_property_views.xml`
- **Implementasi**: Tombol 'Sold' dan 'Cancel' disembunyikan saat property sudah sold/cancelled
- **Kode**:
```xml
<button name="action_sold" type="object" string="Sold" invisible="state in ['sold', 'canceled']"/>
<button name="action_cancel" type="object" string="Cancel" invisible="state in ['sold', 'canceled']"/>
```

#### Invisible pada Garden Fields
- **Status**: Sudah ada dari chapter sebelumnya
- Garden area dan orientation invisible saat tidak ada garden

### 2. Advanced Attributes

#### Invisible pada Offer Buttons
- **File**: `views/estate_property_views.xml`
- **Implementasi**: Tombol 'Accept' dan 'Refuse' disembunyikan setelah status diset
- **Kode**:
```xml
<button name="action_accept" type="object" icon="fa-check" invisible="status"/>
<button name="action_refuse" type="object" icon="fa-times" invisible="status"/>
```

#### Readonly pada Offer List
- **File**: `views/estate_property_views.xml`
- **Implementasi**: Tidak bisa menambah offer saat property sudah offer_accepted/sold/canceled
- **Kode**:
```xml
<field name="offer_ids" readonly="state in ['offer_accepted', 'sold', 'canceled']">
```

### 3. List Editable

#### Estate Property Offer
- **File**: `views/estate_property_offer_views.xml`
- **Implementasi**: List view dapat diedit langsung
- **Kode**:
```xml
<list editable="bottom">
```

#### Estate Property Tag
- **File**: `views/estate_property_tag_views.xml`
- **Implementasi**: List view dapat diedit langsung
- **Kode**:
```xml
<list editable="bottom">
```

### 4. List Decorators

#### Estate Property List
- **File**: `views/estate_property_views.xml`
- **Implementasi**:
  - Offer received: hijau
  - Offer accepted: hijau dan bold
  - Sold: muted (abu-abu)
  - Postcode: optional hide
- **Kode**:
```xml
<list decoration-success="state in ['offer_received', 'offer_accepted']" 
      decoration-bf="state == 'offer_accepted'" 
      decoration-muted="state == 'sold'">
    ...
    <field name="postcode" optional="hide"/>
```

#### Estate Property Offer List
- **File**: `views/estate_property_offer_views.xml`
- **Implementasi**:
  - Refused: merah
  - Accepted: hijau
  - Status: disembunyikan dari kolom (tapi tetap ada untuk decorator)
- **Kode**:
```xml
<list editable="bottom" 
      decoration-success="status == 'accepted'" 
      decoration-danger="status == 'refused'">
    ...
    <field name="status" column_invisible="True"/>
```

## Testing

Jalankan upgrade module:
```bash
.\odoo\odoo-bin -c odoo.conf -u estate
```

## Hasil
- Tombol Sold/Cancel hilang otomatis saat property sudah sold/canceled
- Tombol Accept/Refuse hilang setelah offer diproses
- Offer list readonly saat property dalam status final
- List view offer dan tag bisa diedit inline
- Warna list view memberikan visual feedback berdasarkan status
- Field postcode bisa disembunyikan/ditampilkan sesuai kebutuhan user
