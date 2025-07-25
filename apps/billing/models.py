import uuid
from django.db import models
from decimal import Decimal
from apps.authentication.models import Company
from apps.bookings.models import Booking

class Invoice(models.Model):
    """Corporate invoice generation"""
    
    INVOICE_STATUS = [
        ('Draft', 'Draft'),
        ('Issued', 'Issued'),
        ('Paid', 'Paid'),
        ('Overdue', 'Overdue'),
        ('Cancelled', 'Cancelled'),
    ]
    
    invoice_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='invoices')
    invoice_number = models.CharField(max_length=50, unique=True)
    invoice_period_start = models.DateField()
    invoice_period_end = models.DateField()
    
    currency = models.CharField(max_length=3, default='USD')
    subtotal_amount = models.DecimalField(max_digits=12, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    invoice_status = models.CharField(max_length=20, choices=INVOICE_STATUS, default='Draft')
    issued_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    paid_date = models.DateField(null=True, blank=True)
    
    # Billing details
    billing_address = models.JSONField(default=dict)
    tax_details = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'invoice'
        indexes = [
            models.Index(fields=['company', 'invoice_period_start']),
            models.Index(fields=['invoice_status']),
        ]
    
    def generate_invoice_number(self):
        """Generate unique invoice number"""
        from django.utils import timezone
        year_month = timezone.now().strftime('%Y%m')
        count = Invoice.objects.filter(
            invoice_number__startswith=f'INV-{year_month}'
        ).count() + 1
        return f'INV-{year_month}-{count:04d}'
    
    def calculate_totals(self):
        """Calculate invoice totals"""
        line_items = self.line_items.all()
        self.subtotal_amount = sum(item.total_amount for item in line_items)
        
        # Calculate tax (example: 10% VAT)
        tax_rate = Decimal('0.10')
        self.tax_amount = self.subtotal_amount * tax_rate
        self.total_amount = self.subtotal_amount + self.tax_amount
        
        self.save()

class InvoiceLineItem(models.Model):
    """Invoice line items"""
    
    line_item_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='line_items')
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Optional booking reference
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        self.total_amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)

class InvoiceBookingMap(models.Model):
    """Many-to-many relationship between invoices and bookings"""
    
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'invoice_booking_map'
        unique_together = ['invoice', 'booking']

class BillingCycle(models.Model):
    """Automated billing cycle management"""
    
    cycle_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='billing_cycles')
    cycle_start_date = models.DateField()
    cycle_end_date = models.DateField()
    
    # Billing configuration
    auto_generate_invoice = models.BooleanField(default=True)
    payment_terms_days = models.IntegerField(default=30)
    
    # Status tracking
    invoice_generated = models.BooleanField(default=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def generate_invoice(self):
        """Generate invoice for this billing cycle"""
        if self.invoice_generated:
            return self.invoice
        
        # Get all bookings for this company in the cycle period
        bookings = Booking.objects.filter(
            company=self.company,
            booking_start_time__date__range=[self.cycle_start_date, self.cycle_end_date],
            booking_status_code='Completed',
            payment_status_code='Paid'
        )
        
        if not bookings.exists():
            return None
        
        # Create invoice
        invoice = Invoice.objects.create(
            company=self.company,
            invoice_number=Invoice().generate_invoice_number(),
            invoice_period_start=self.cycle_start_date,
            invoice_period_end=self.cycle_end_date,
            subtotal_amount=0,
            total_amount=0
        )
        
        # Create line items
        for booking in bookings:
            InvoiceLineItem.objects.create(
                invoice=invoice,
                description=f"Coworking space booking - {booking.venue.venue_name}",
                quantity=1,
                unit_price=booking.total_price,
                booking=booking
            )
            
            # Create booking mapping
            InvoiceBookingMap.objects.create(
                invoice=invoice,
                booking=booking
            )
        
        # Calculate totals
        invoice.calculate_totals()
        
        # Update cycle
        self.invoice = invoice
        self.invoice_generated = True
        self.save()
        
        return invoice

class UsageReport(models.Model):
    """Usage tracking and reporting"""
    
    report_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='usage_reports')
    report_period_start = models.DateField()
    report_period_end = models.DateField()
    
    # Usage metrics
    total_bookings = models.IntegerField(default=0)
    total_hours = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Breakdown by venue type
    usage_breakdown = models.JSONField(default=dict)
    
    # Top users
    top_users = models.JSONField(default=list)
    
    generated_at = models.DateTimeField(auto_now_add=True)
    
    def generate_report(self):
        """Generate usage report"""
        bookings = Booking.objects.filter(
            company=self.company,
            booking_start_time__date__range=[self.report_period_start, self.report_period_end],
            booking_status_code='Completed'
        ).select_related('venue', 'user__userprofile')
        
        self.total_bookings = bookings.count()
        self.total_hours = sum(
            (booking.booking_end_time - booking.booking_start_time).total_seconds() / 3600
            for booking in bookings
        )
        self.total_amount = sum(booking.total_price for booking in bookings)
        
        # Venue type breakdown
        venue_breakdown = {}
        for booking in bookings:
            venue_type = booking.venue.venue_type_code
            if venue_type not in venue_breakdown:
                venue_breakdown[venue_type] = {
                    'count': 0,
                    'hours': 0,
                    'amount': 0
                }
            
            duration = (booking.booking_end_time - booking.booking_start_time).total_seconds() / 3600
            venue_breakdown[venue_type]['count'] += 1
            venue_breakdown[venue_type]['hours'] += duration
            venue_breakdown[venue_type]['amount'] += float(booking.total_price)
        
        self.usage_breakdown = venue_breakdown
        
        # Top users
        user_usage = {}
        for booking in bookings:
            user_id = str(booking.user.id)
            user_name = booking.user.userprofile.full_name
            
            if user_id not in user_usage:
                user_usage[user_id] = {
                    'name': user_name,
                    'bookings': 0,
                    'hours': 0,
                    'amount': 0
                }
            
            duration = (booking.booking_end_time - booking.booking_start_time).total_seconds() / 3600
            user_usage[user_id]['bookings'] += 1
            user_usage[user_id]['hours'] += duration
            user_usage[user_id]['amount'] += float(booking.total_price)
        
        # Sort by amount and take top 10
        self.top_users = sorted(
            user_usage.values(),
            key=lambda x: x['amount'],
            reverse=True
        )[:10]
        
        self.save()