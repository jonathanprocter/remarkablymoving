#!/usr/bin/env python3
"""
reMarkable Pro Calendar PDF Generator
Optimized for reMarkable Pro (2160x1620 landscape, 1620x2160 portrait)
"""

import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, portrait
from reportlab.lib.units import inch
from reportlab.lib import colors
import json
import sys

# reMarkable Pro specifications
REMARKABLE_WIDTH = 1620
REMARKABLE_HEIGHT = 2160

# Define page sizes
landscape_size = (REMARKABLE_HEIGHT, REMARKABLE_WIDTH)
portrait_size = (REMARKABLE_WIDTH, REMARKABLE_HEIGHT)

def create_weekly_view_with_events(c, week_start_date, events, landscape_size):
    """Create the landscape weekly overview page"""
    c.setPageSize(landscape_size)
    c.setFont("Helvetica-Bold", 36)
    c.drawString(inch, landscape_size[1] - inch, f"WEEKLY OVERVIEW - WEEK OF {week_start_date.strftime('%B %d, %Y').upper()}")
    
    # Draw weekly grid
    days = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
    x_start = inch
    y_start = landscape_size[1] - 2 * inch
    col_width = (landscape_size[0] - 2 * inch) / 8
    row_height = (landscape_size[1] - 4 * inch) / 31
    
    # Draw header with clickable day links
    c.setFont("Helvetica-Bold", 24)
    for i, day in enumerate(days):
        x_pos = x_start + (i + 1) * col_width + 20
        c.drawString(x_pos, y_start + 10, day)
        # Add clickable links to daily pages
        link_rect = (x_start + (i + 1) * col_width, y_start, 
                    x_start + (i + 2) * col_width, y_start + row_height)
        c.linkRect(day, f"day_{i+1}", link_rect)
    
    # Draw time slots (07:00-22:00 in military time)
    c.setFont("Helvetica", 18)
    for i in range(31):  # 31 half-hour slots from 07:00 to 22:00
        time = f"{(i // 2) + 7:02d}:{30 * (i % 2):02d}"
        c.drawString(x_start + 10, y_start - i * row_height, time)
    
    # Draw grid lines
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    
    # Vertical lines (extend to bottom as per requirements)
    for i in range(8):
        c.line(x_start + i * col_width, y_start + row_height, 
               x_start + i * col_width, y_start - 30 * row_height)
    
    # Horizontal lines
    for i in range(32):
        c.line(x_start, y_start - (i-1) * row_height, 
               x_start + 8 * col_width, y_start - (i-1) * row_height)
    
    # Add events to weekly view
    c.setFont("Helvetica", 12)
    for event in events:
        event_date = datetime.datetime.strptime(event['date'], '%Y-%m-%d').date()
        day_offset = (event_date - week_start_date).days
        
        if 0 <= day_offset < 7:
            start_time = datetime.datetime.strptime(event['start_time'], '%H:%M').time()
            end_time = datetime.datetime.strptime(event['end_time'], '%H:%M').time()
            
            # Calculate position
            start_hour = start_time.hour + start_time.minute / 60
            end_hour = end_time.hour + end_time.minute / 60
            
            if 7 <= start_hour <= 22:
                start_row = int((start_hour - 7) * 2)
                end_row = int((end_hour - 7) * 2)
                
                event_x = x_start + (day_offset + 1) * col_width + 5
                event_y_start = y_start - start_row * row_height
                event_height = (end_row - start_row) * row_height
                
                # Draw event block (proportional to duration)
                c.setFillColor(colors.lightblue)
                c.rect(event_x, event_y_start - event_height, col_width - 10, event_height, fill=1)
                
                # Add event text
                c.setFillColor(colors.black)
                c.drawString(event_x + 5, event_y_start - 15, event['title'][:20])
    
    c.showPage()

def create_daily_view_with_events(c, date, day_name, page_num, day_events, portrait_size):
    """Create portrait daily view pages"""
    c.setPageSize(portrait_size)
    c.setFont("Helvetica-Bold", 36)
    c.drawString(inch, portrait_size[1] - inch, f"{day_name.upper()} - {date.strftime('%B %d, %Y')}")
    
    # Add link back to weekly view (bidirectional linking)
    c.setFont("Helvetica", 18)
    c.drawString(inch, portrait_size[1] - 1.5*inch, "← Back to Weekly Overview")
    c.linkRect("← Back to Weekly", "weekly_view", (inch, portrait_size[1] - 1.5*inch, 3*inch, portrait_size[1] - inch))
    
    # Draw daily schedule
    x_start = inch
    y_start = portrait_size[1] - 2 * inch
    row_height = (portrait_size[1] - 4 * inch) / 31
    
    # Draw time slots (07:00-22:00 in military time with 30-minute intervals)
    c.setFont("Helvetica", 18)
    for i in range(31):
        time = f"{(i // 2) + 7:02d}:{30 * (i % 2):02d}"
        c.drawString(x_start + 10, y_start - i * row_height, time)
    
    # Draw grid lines
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    c.line(x_start + 1.5*inch, y_start + row_height, 
           x_start + 1.5*inch, y_start - 30 * row_height)
    
    for i in range(32):
        c.line(x_start, y_start - (i-1) * row_height, 
               portrait_size[0] - inch, y_start - (i-1) * row_height)
    
    # Add events to daily view
    c.setFont("Helvetica", 14)
    for event in day_events:
        start_time = datetime.datetime.strptime(event['start_time'], '%H:%M').time()
        end_time = datetime.datetime.strptime(event['end_time'], '%H:%M').time()
        
        start_hour = start_time.hour + start_time.minute / 60
        end_hour = end_time.hour + end_time.minute / 60
        
        if 7 <= start_hour <= 22:
            start_row = int((start_hour - 7) * 2)
            end_row = int((end_hour - 7) * 2)
            
            event_x = x_start + 1.5*inch + 10
            event_y_start = y_start - start_row * row_height
            event_height = (end_row - start_row) * row_height
            event_width = portrait_size[0] - x_start - 1.5*inch - 2*inch
            
            # Draw event block (proportional to duration)
            c.setFillColor(colors.lightblue)
            c.rect(event_x, event_y_start - event_height, event_width, event_height, fill=1)
            
            # Add event text
            c.setFillColor(colors.black)
            c.drawString(event_x + 5, event_y_start - 20, event['title'])
            if event.get('description'):
                c.setFont("Helvetica", 12)
                c.drawString(event_x + 5, event_y_start - 35, event['description'][:50])
                c.setFont("Helvetica", 14)
    
    c.showPage()

def generate_calendar_pdf(filename, week_start_date, events):
    """Generate the complete PDF with weekly and daily views"""
    c = canvas.Canvas(filename)
    c.setAuthor("reMarkable Calendar Exporter")
    c.setTitle("Weekly Calendar Overview - reMarkable Pro Optimized")
    
    # Create weekly view with events
    c.bookmarkPage("weekly_view")
    c.addOutlineEntry("Weekly Overview", "weekly_view", 0, 0)
    create_weekly_view_with_events(c, week_start_date, events, landscape_size)
    
    # Create daily views with events
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    for i, day in enumerate(days):
        date = week_start_date + datetime.timedelta(days=i)
        day_events = [e for e in events if e.get('date') == date.strftime('%Y-%m-%d')]
        c.bookmarkPage(f"day_{i+1}")
        c.addOutlineEntry(day, f"day_{i+1}", 1, 0)
        create_daily_view_with_events(c, date, day, i + 2, day_events, portrait_size)
    
    c.save()
    print(f"PDF generated successfully: {filename}")

def main():
    """Main function to generate calendar PDF"""
    # Get current week's Monday as default
    today = datetime.date.today()
    week_start_date = today - datetime.timedelta(days=today.weekday())
    
    # Sample events (replace with your own data)
    events = [
        {
            "title": "Team Meeting",
            "date": week_start_date.strftime('%Y-%m-%d'),
            "start_time": "09:00",
            "end_time": "10:30",
            "description": "Weekly team sync"
        },
        {
            "title": "Project Review",
            "date": (week_start_date + datetime.timedelta(days=2)).strftime('%Y-%m-%d'),
            "start_time": "14:00",
            "end_time": "15:30",
            "description": "Quarterly project review"
        }
    ]
    
    # Generate PDF
    filename = f"remarkable_calendar_{week_start_date.strftime('%Y%m%d')}.pdf"
    generate_calendar_pdf(filename, week_start_date, events)

if __name__ == "__main__":
    main()

