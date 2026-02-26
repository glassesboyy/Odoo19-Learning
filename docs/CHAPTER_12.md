# Chapter 12: Inline Views

## Konsep
Inline views memungkinkan menampilkan tree view dari multiple records di dalam form view. Ini berguna untuk menampilkan data relasional (One2many/Many2many) secara inline tanpa perlu membuka view terpisah.

## Struktur Dasar
```xml
<field name="one2many_field">
    <tree>
        <field name="field_1"/>
        <field name="field_2"/>
    </tree>
</field>
```

## Implementasi

### 1. Inline Tree View untuk Offers
Form view `estate.property` sudah memiliki inline tree view untuk menampilkan offers:

**File**: `views/estate_property_views.xml`
```xml
<page string="Offers">
    <field name="offer_ids">
        <tree>
            <field name="price"/>
            <field name="partner_id"/>
            <field name="validity"/>
            <field name="date_deadline"/>
            <field name="status"/>
            <button name="action_accept" type="object" icon="fa-check"/>
            <button name="action_refuse" type="object" icon="fa-times"/>
        </tree>
    </field>
</page>
```

### 2. Property Type dengan Inline Properties

**Model**: `models/estate_property_type.py`
- Menambahkan field `property_ids` (One2many) untuk menampilkan semua properties yang menggunakan type tersebut

```python
property_ids = fields.One2many('estate.property', 'property_type_id', string='Properties')
```

**View**: `views/estate_property_type_views.xml`
- Menambahkan notebook dengan page "Properties"
- Inline tree view menampilkan: name, expected_price, dan state

```xml
<notebook>
    <page string="Properties">
        <field name="property_ids">
            <tree>
                <field name="name"/>
                <field name="expected_price"/>
                <field name="state"/>
            </tree>
        </field>
    </page>
</notebook>
```

## Hasil
- Form view estate.property menampilkan daftar offers secara inline
- Form view estate.property.type menampilkan daftar properties yang menggunakan type tersebut secara inline
- User dapat melihat dan mengedit relational data tanpa membuka window baru
