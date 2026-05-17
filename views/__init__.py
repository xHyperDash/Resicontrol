"""
Views package for ResiControl UI.

Contains all view modules for the application:
- base.py: Shared CTkFrame components and utilities
- navigation.py: Sidebar navigation logic
- dashboard.py: Dashboard/metrics view
- residents.py: Resident management view
- visitors.py: Visitor registration view
- parking.py: Parking lot management view
- history.py: Access history view
- incidents.py: Incident logging view
- reports.py: PDF report generation view
- backup.py: Backup management view
- users.py: User management view (admin only)
- qr_scanner.py: QR code scanning view
"""

from views.base import BaseView
from views.navigation import get_menu_items, create_sidebar_menu