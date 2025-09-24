# Overview

This is a Django-based Point of Sale (POS) and Inventory Management System designed for small businesses. The application provides a comprehensive solution for sales transactions, inventory tracking, customer management, and business reporting. It features a modern web interface with barcode scanning capabilities, GST (tax) compliance, and secure inventory management with password protection.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Backend Architecture
- **Framework**: Django 5.2.6 with Python as the primary backend technology
- **Database**: SQLite (default Django setup) for data persistence
- **Apps Structure**: Modular Django app design with four main apps:
  - `sales`: POS interface, invoice management, and customer handling
  - `inventory`: Product management, stock tracking, and barcode generation
  - `profiles`: Shop configuration and settings management
  - `reports`: Business analytics and data export functionality

## Frontend Architecture
- **Template Engine**: Django templates with Jinja2-style templating
- **CSS Framework**: Bootstrap 5 for responsive UI design
- **JavaScript**: Vanilla JavaScript for POS interactions and barcode scanning
- **Styling**: Custom CSS with CSS custom properties for theming

## Data Models
- **Product Management**: Products with SKU, barcode, pricing, tax rates, and stock quantities
- **Sales System**: Invoices, invoice items, and customer records with GST compliance
- **Inventory Tracking**: Stock movements with reasons (purchase, adjustment, sale)
- **Shop Profile**: Singleton pattern for shop configuration and settings

## Authentication & Security
- **Session-based Authentication**: Custom inventory password protection using Django's session framework
- **Password Hashing**: Django's built-in password hashing for inventory access
- **Access Control**: Protected inventory management sections requiring authentication

## Business Logic Features
- **Tax Calculations**: Automatic GST/tax calculations with configurable rates
- **Stock Management**: Real-time inventory tracking with low stock alerts
- **Invoice Generation**: Sequential invoice numbering with customizable prefixes
- **Barcode Support**: Product barcode generation and scanning capabilities
- **Multi-format Printing**: A4 and thermal receipt printing support

## Database Design
- **Decimal Precision**: Financial calculations using Django's DecimalField for accuracy
- **Audit Trail**: Stock movements tracking for inventory changes
- **Flexible Customer System**: Support for both registered customers and walk-in sales
- **Extensible Product System**: Product variants support through SKU and barcode systems

# External Dependencies

## Core Framework Dependencies
- **Django 5.2.6**: Web framework for backend development
- **crispy-forms & crispy-bootstrap5**: Enhanced form rendering with Bootstrap styling

## Python Libraries
- **openpyxl**: Excel file generation for data export functionality
- **Pillow**: Image processing for shop logos and barcode generation (implied by ImageField usage)

## Frontend Dependencies
- **Bootstrap 5.3.0**: CSS framework loaded via CDN for responsive design
- **Font Awesome**: Icon library for UI elements (referenced in templates)

## Development Environment
- **SQLite**: Default database for development and small-scale deployment
- **Django's built-in server**: Development server for local testing

## Potential Integration Points
- **Barcode Scanner Hardware**: JavaScript-based barcode scanning interface
- **Thermal Printer Support**: Print templates optimized for thermal receipt printers
- **Export Capabilities**: XLSX export functionality for reports and data analysis