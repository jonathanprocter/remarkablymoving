#!/usr/bin/env python3
"""
reMarkable Pro Move Weekly Planner PDF Generator
Optimized for reMarkable Pro Move tablet (229.5 x 297mm / Letter size)
Exact implementation following comprehensive specification
"""

import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import mm, inch
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import json
import sys

# Page dimensions - Letter size for reMarkable compatibility
PAGE_WIDTH = 215.9 * mm  # 8.5 inches
PAGE_HEIGHT = 279.4 * mm  # 11 inches
MARGIN = 10 * mm  # 10mm margins for gesture zones

# Colors for e-ink optimization
BLACK = colors.black
WHITE = colors.white
LIGHT_GRAY = colors.Color(red=0.95, green=0.95, blue=0.95)  # 5% gray for alternating bands

# Button specifications
BUTTON_MIN_SIZE = 10 * mm  # Minimum 10mm x 10mm tap target
BUTTON_PADDING = 3 * mm  # 3mm internal padding
BUTTON_SPACING = 5 * mm  # 5mm between buttons

def create_weekly_overview_page(c, week_start_date, events):
    """Create Page 1: Weekly overview grid (Monday-Sunday)"""
    c.setPageSize(letter)
    
    # Header bar with title
    c.setFont("Helvetica-Bold", 14)
    header_text = f"WEEK OF {week_start_date.strftime('%B %d, %Y').upper()}"
    c.drawString(MARGIN, PAGE_HEIGHT - MARGIN - 5*mm, header_text)
    
    # Calculate grid dimensions
    grid_top = PAGE_HEIGHT - MARGIN - 15*mm
    grid_bottom = MARGIN + 10*mm
    grid_height = grid_top - grid_bottom
    
    # Time column width (for times 07:00-22:00)
    time_col_width = 15*mm
    
    # Day columns - equal width for all days
    available_width = PAGE_WIDTH - 2*MARGIN - time_col_width
    day_col_width = available_width / 7
    
    # Hour rows - 16 hours (7:00 AM to 10:00 PM)
    num_hours = 16  # 7:00-22:00
    row_height = grid_height / (num_hours + 1)  # +1 for header row
    
    # Day headers with navigation links
    days = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
    full_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    c.setFont("Helvetica-Bold", 10)
    c.setLineWidth(2)  # 2pt for major divisions
    
    # Draw day header cells with clickable links
    for i, (day, full_day) in enumerate(zip(days, full_days)):
        x = MARGIN + time_col_width + i * day_col_width
        y = grid_top - row_height
        
        # Draw header cell
        c.rect(x, y, day_col_width, row_height)
        
        # Add day text with page number indicator
        header_text = f"📅 {day} - p.{i+2}"
        text_width = c.stringWidth(header_text, "Helvetica-Bold", 10)
        c.drawString(x + (day_col_width - text_width)/2, y + row_height/2 - 2*mm, header_text)
        
        # Create clickable link to daily page
        c.linkAbsolute("", f"day_{i+1}", 
                      (x, y, x + day_col_width, y + row_height), 
                      Border='[0 0 0]')
    
    # Draw time column header
    c.rect(MARGIN, grid_top - row_height, time_col_width, row_height)
    c.drawString(MARGIN + 2*mm, grid_top - row_height/2 - 2*mm, "TIME")
    
    # Draw time slots and grid
    c.setFont("Helvetica", 10)
    c.setLineWidth(1)  # 1pt for hour divisions
    
    for hour_idx in range(num_hours):
        hour = 7 + hour_idx
        y = grid_top - (hour_idx + 2) * row_height  # +2 to skip header row
        
        # Time label (military format)
        time_str = f"{hour:02d}:00"
        c.drawString(MARGIN + 2*mm, y + row_height/2 - 2*mm, time_str)
        
        # Alternating gray bands for visual hierarchy
        if hour_idx % 2 == 1:
            c.setFillColor(LIGHT_GRAY)
            for day_idx in range(7):
                x = MARGIN + time_col_width + day_idx * day_col_width
                c.rect(x, y, day_col_width, row_height, fill=1, stroke=0)
            c.setFillColor(WHITE)
        
        # Draw horizontal grid line
        c.line(MARGIN, y, PAGE_WIDTH - MARGIN, y)
    
    # Draw vertical grid lines
    c.setLineWidth(2)  # Major divisions
    c.line(MARGIN, grid_top, MARGIN, grid_bottom)  # Left border
    c.line(MARGIN + time_col_width, grid_top, MARGIN + time_col_width, grid_bottom)  # Time column separator
    
    c.setLineWidth(1)  # Day column divisions
    for i in range(1, 8):
        x = MARGIN + time_col_width + i * day_col_width
        c.line(x, grid_top, x, grid_bottom)
    
    # Draw bottom border
    c.setLineWidth(2)
    c.line(MARGIN, grid_bottom, PAGE_WIDTH - MARGIN, grid_bottom)
    
    # Add events to the weekly grid
    c.setFont("Helvetica", 8)
    for event in events:
        event_date_str = event.get('date')
        if not event_date_str:
            continue
        
        try:
            event_date = datetime.datetime.strptime(event_date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            continue
        
        day_offset = (event_date - week_start_date).days
        
        if 0 <= day_offset < 7:
            start_time_str = event.get('start_time', event.get('time', '09:00'))
            
            try:
                start_time = datetime.datetime.strptime(start_time_str, '%H:%M').time()
            except (ValueError, TypeError):
                continue
            
            if 7 <= start_time.hour <= 22:
                # Calculate position
                hour_offset = start_time.hour - 7
                x = MARGIN + time_col_width + day_offset * day_col_width + 2*mm
                y = grid_top - (hour_offset + 2) * row_height + row_height - 4*mm
                
                # Add event with link indicator
                title = event.get('title', event.get('summary', 'Event'))[:20]
                c.drawString(x, y, f"{title} →")
                
                # Create link to specific time on daily page
                link_rect = (x, y - 2*mm, x + day_col_width - 4*mm, y + 4*mm)
                c.linkAbsolute("", f"day_{day_offset+1}_time_{start_time.hour}", 
                              link_rect, Border='[0 0 0]')
    
    c.showPage()

def create_daily_page(c, date, day_name, page_num, day_events, week_start_date):
    """Create Pages 2-8: Individual daily pages with three-column layout"""
    c.setPageSize(letter)
    
    # Add bookmark for this day
    c.bookmarkPage(f"day_{page_num-1}")
    
    # Navigation bar at top
    nav_y = PAGE_HEIGHT - MARGIN - 10*mm
    
    # Previous day button [←]
    if page_num > 2:
        c.setLineWidth(2)
        c.rect(MARGIN, nav_y, 15*mm, 10*mm)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(MARGIN + 5*mm, nav_y + 3*mm, "←")
        c.linkAbsolute("", f"day_{page_num-2}", 
                      (MARGIN, nav_y, MARGIN + 15*mm, nav_y + 10*mm), 
                      Border='[0 0 0]')
    
    # Week button [WEEK]
    week_btn_x = MARGIN + 20*mm
    c.setLineWidth(2)
    c.rect(week_btn_x, nav_y, 25*mm, 10*mm)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(week_btn_x + 5*mm, nav_y + 3*mm, "WEEK")
    c.linkAbsolute("", "weekly_view", 
                  (week_btn_x, nav_y, week_btn_x + 25*mm, nav_y + 10*mm), 
                  Border='[0 0 0]')
    
    # Next day button [→]
    if page_num < 8:
        next_btn_x = week_btn_x + 30*mm
        c.rect(next_btn_x, nav_y, 15*mm, 10*mm)
        c.drawString(next_btn_x + 5*mm, nav_y + 3*mm, "→")
        c.linkAbsolute("", f"day_{page_num}", 
                      (next_btn_x, nav_y, next_btn_x + 15*mm, nav_y + 10*mm), 
                      Border='[0 0 0]')
    
    # Day title
    c.setFont("Helvetica-Bold", 14)
    title_text = f"{day_name.upper()} - {date.strftime('%B %d, %Y')}"
    c.drawString(MARGIN + 80*mm, nav_y + 3*mm, title_text)
    
    # Three-column layout
    content_top = nav_y - 5*mm
    content_bottom = MARGIN + 15*mm  # Leave space for quick jump footer
    content_height = content_top - content_bottom
    
    # Column widths
    time_col_width = PAGE_WIDTH * 0.2  # 20% for time slots
    main_col_width = PAGE_WIDTH * 0.6  # 60% for appointments
    notes_col_width = PAGE_WIDTH * 0.2  # 20% for notes
    
    # Time column (30-minute intervals from 7:00 to 22:00)
    c.setFont("Helvetica", 8)
    c.setLineWidth(0.5)
    
    num_slots = 31  # 7:00-22:00 in 30-minute intervals
    slot_height = content_height / num_slots
    
    for slot_idx in range(num_slots):
        hour = 7 + slot_idx // 2
        minute = (slot_idx % 2) * 30
        y = content_top - slot_idx * slot_height
        
        # Add bookmark for hourly navigation from weekly view
        if minute == 0:
            c.bookmarkPage(f"day_{page_num-1}_time_{hour}")
        
        # Time label
        time_str = f"{hour:02d}:{minute:02d}"
        c.drawString(MARGIN + 2*mm, y - slot_height/2 - 1*mm, time_str)
        
        # Business hours highlighting (9:00-17:00)
        if 9 <= hour < 17:
            c.setFillColor(LIGHT_GRAY)
            c.rect(MARGIN + time_col_width, y - slot_height, main_col_width, slot_height, 
                  fill=1, stroke=0)
            c.setFillColor(WHITE)
        
        # Horizontal lines
        if minute == 0:
            c.setLineWidth(1)  # Bold lines at hour marks
        else:
            c.setLineWidth(0.3)  # Dotted lines between 30-minute marks
            c.setDash(1, 2)
        
        c.line(MARGIN + time_col_width, y, PAGE_WIDTH - MARGIN - notes_col_width, y)
        c.setDash()  # Reset dash
    
    # Vertical column separators
    c.setLineWidth(1)
    c.line(MARGIN + time_col_width, content_top, MARGIN + time_col_width, content_bottom)
    c.line(PAGE_WIDTH - MARGIN - notes_col_width, content_top, 
           PAGE_WIDTH - MARGIN - notes_col_width, content_bottom)
    
    # Notes section header
    c.setFont("Helvetica-Bold", 10)
    c.drawString(PAGE_WIDTH - MARGIN - notes_col_width + 2*mm, content_top - 5*mm, "NOTES")
    
    # Add horizontal ruled lines in notes section
    c.setLineWidth(0.3)
    for i in range(1, 20):
        y = content_top - 10*mm - i * 10*mm
        if y > content_bottom:
            c.line(PAGE_WIDTH - MARGIN - notes_col_width + 2*mm, y, 
                  PAGE_WIDTH - MARGIN - 2*mm, y)
    
    # Quick jump footer
    footer_y = MARGIN
    days_abbr = ["M", "T", "W", "T", "F", "S", "S"]
    
    c.setFont("Helvetica-Bold", 10)
    c.setLineWidth(1)
    
    for i, day_abbr in enumerate(days_abbr):
        btn_x = MARGIN + i * (BUTTON_MIN_SIZE + BUTTON_SPACING)
        
        # Highlight current day
        if i == page_num - 2:
            c.setLineWidth(3)  # Bold border for current day
        else:
            c.setLineWidth(1)
        
        # Draw button
        c.rect(btn_x, footer_y, BUTTON_MIN_SIZE, BUTTON_MIN_SIZE)
        
        # Day letter
        c.drawString(btn_x + 3*mm, footer_y + 6*mm, day_abbr)
        
        # Page number below
        c.setFont("Helvetica", 6)
        c.drawString(btn_x + 4*mm, footer_y + 2*mm, str(i + 2))
        c.setFont("Helvetica-Bold", 10)
        
        # Create link to that day
        if i != page_num - 2:  # Don't link to current page
            c.linkAbsolute("", f"day_{i+1}", 
                          (btn_x, footer_y, btn_x + BUTTON_MIN_SIZE, footer_y + BUTTON_MIN_SIZE), 
                          Border='[0 0 0]')
    
    # Add events to the daily schedule
    c.setFont("Helvetica", 9)
    for event in day_events:
        start_time_str = event.get('start_time', event.get('time', '09:00'))
        
        try:
            start_time = datetime.datetime.strptime(start_time_str, '%H:%M').time()
        except (ValueError, TypeError):
            continue
        
        if 7 <= start_time.hour <= 22:
            # Calculate position
            slot_idx = (start_time.hour - 7) * 2 + (start_time.minute // 30)
            y = content_top - slot_idx * slot_height - slot_height/2
            
            # Draw event in main column
            title = event.get('title', event.get('summary', 'Event'))
            c.drawString(MARGIN + time_col_width + 2*mm, y, title)
    
    c.showPage()

def generate_calendar_pdf(filename, week_start_date, events):
    """Generate the complete 8-page PDF following exact specifications"""
    c = canvas.Canvas(filename)
    c.setAuthor("reMarkable Calendar Exporter")
    c.setTitle("Weekly Planner - reMarkable Pro Move Optimized")
    c.setSubject("Interactive 8-page weekly planner with bi-directional navigation")
    
    # Create Page 1: Weekly overview
    c.bookmarkPage("weekly_view")
    c.addOutlineEntry("Weekly Overview", "weekly_view", 0, 0)
    create_weekly_overview_page(c, week_start_date, events)
    
    # Create Pages 2-8: Daily pages (Monday through Sunday)
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    for i, day in enumerate(days):
        date = week_start_date + datetime.timedelta(days=i)
        
        # Filter events for this specific day
        day_events = []
        for event in events:
            event_date_str = event.get('date')
            if event_date_str:
                try:
                    event_date = datetime.datetime.strptime(event_date_str, '%Y-%m-%d').date()
                    if event_date == date:
                        day_events.append(event)
                except (ValueError, TypeError):
                    continue
        
        # Add to outline
        c.addOutlineEntry(day, f"day_{i+1}", 1, 0)
        
        # Create the daily page
        create_daily_page(c, date, day, i + 2, day_events, week_start_date)
    
    c.save()
    
    print(f"✅ PDF generated successfully: {filename}")
    print(f"   📋 Specifications met:")
    print(f"   - 8 pages (1 weekly overview + 7 daily pages)")
    print(f"   - Letter size (8.5\" x 11\") for reMarkable compatibility")
    print(f"   - Weekly: 07:00-22:00 in 1-hour increments")
    print(f"   - Daily: 30-minute intervals with 3-column layout")
    print(f"   - Bi-directional navigation with proper button sizes")
    print(f"   - E-ink optimized (max 5% gray, high contrast)")
    print(f"   - Interactive PDF with embedded links")
    
    return filename

def transform_google_calendar_events(google_events):
    """Transform Google Calendar events to the format expected by the PDF generator"""
    transformed_events = []
    
    for event in google_events:
        # Handle all-day events and regular events
        if 'dateTime' in event.get('start', {}):
            start_dt = datetime.datetime.fromisoformat(event['start']['dateTime'].replace('Z', '+00:00'))
            end_dt = datetime.datetime.fromisoformat(event['end']['dateTime'].replace('Z', '+00:00'))
            date_str = start_dt.strftime('%Y-%m-%d')
            start_time = start_dt.strftime('%H:%M')
            end_time = end_dt.strftime('%H:%M')
            duration = int((end_dt - start_dt).total_seconds() / 60)
        elif 'date' in event.get('start', {}):
            # All-day event
            date_str = event['start']['date']
            start_time = '09:00'
            end_time = '10:00'
            duration = 60
        else:
            continue
        
        transformed_event = {
            'title': event.get('summary', 'Untitled Event'),
            'date': date_str,
            'start_time': start_time,
            'end_time': end_time,
            'duration': duration,
            'description': event.get('description', ''),
            'location': event.get('location', ''),
            'type': 'appointment'
        }
        
        transformed_events.append(transformed_event)
    
    return transformed_events

def generate_pdf_from_week_data(week_data, start_date, output_filename=None):
    """Generate PDF from week data (compatible with existing API)"""
    # Parse start date
    if isinstance(start_date, str):
        week_start = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
    else:
        week_start = start_date
    
    # Extract and transform events
    all_events = []
    
    # Handle events in the format from the JavaScript generator
    if 'events' in week_data:
        for day_key, day_events in week_data['events'].items():
            # Calculate the date for this day
            day_map = {
                'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                'friday': 4, 'saturday': 5, 'sunday': 6
            }
            
            if day_key.lower() in day_map:
                day_offset = day_map[day_key.lower()]
                event_date = week_start + datetime.timedelta(days=day_offset)
                
                for event in day_events:
                    transformed_event = {
                        'title': event.get('title', 'Untitled'),
                        'date': event_date.strftime('%Y-%m-%d'),
                        'start_time': event.get('time', '09:00'),
                        'duration': event.get('duration', 60),
                        'description': event.get('description', ''),
                        'type': event.get('type', 'appointment')
                    }
                    
                    # Calculate end time from duration
                    start_time = datetime.datetime.strptime(transformed_event['start_time'], '%H:%M').time()
                    end_hour = start_time.hour + (start_time.minute + transformed_event['duration']) // 60
                    end_minute = (start_time.minute + transformed_event['duration']) % 60
                    transformed_event['end_time'] = f"{end_hour:02d}:{end_minute:02d}"
                    
                    all_events.append(transformed_event)
    
    # Generate output filename if not provided
    if not output_filename:
        output_filename = f"remarkable_planner_{week_start.strftime('%Y%m%d')}.pdf"
    
    # Generate the PDF
    generate_calendar_pdf(output_filename, week_start, all_events)
    
    return output_filename

def main():
    """Main function to generate calendar PDF"""
    # Get current week's Monday as default
    today = datetime.date.today()
    week_start_date = today - datetime.timedelta(days=today.weekday())
    
    # Test events spanning the week
    events = [
        {
            "title": "Morning Standup",
            "date": week_start_date.strftime('%Y-%m-%d'),
            "start_time": "09:00",
            "end_time": "09:30",
            "description": "Daily team sync"
        },
        {
            "title": "Client Meeting",
            "date": week_start_date.strftime('%Y-%m-%d'),
            "start_time": "14:00",
            "end_time": "15:00",
            "description": "Q3 Review"
        },
        {
            "title": "Lunch & Learn",
            "date": (week_start_date + datetime.timedelta(days=2)).strftime('%Y-%m-%d'),
            "start_time": "12:00",
            "end_time": "13:00",
            "description": "Tech talk"
        },
        {
            "title": "Sprint Planning",
            "date": (week_start_date + datetime.timedelta(days=3)).strftime('%Y-%m-%d'),
            "start_time": "10:00",
            "end_time": "11:30",
            "description": "Next sprint planning"
        },
        {
            "title": "Team Outing",
            "date": (week_start_date + datetime.timedelta(days=4)).strftime('%Y-%m-%d'),
            "start_time": "17:00",
            "end_time": "19:00",
            "description": "Friday happy hour"
        }
    ]
    
    # Generate PDF
    filename = f"remarkable_planner_{week_start_date.strftime('%Y%m%d')}.pdf"
    generate_calendar_pdf(filename, week_start_date, events)

if __name__ == "__main__":
    main()