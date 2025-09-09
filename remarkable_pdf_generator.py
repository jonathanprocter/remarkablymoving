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
from typing import List, Dict, Optional, Tuple
import os

# reMarkable Pro specifications
REMARKABLE_WIDTH = 1620
REMARKABLE_HEIGHT = 2160

# Define page sizes
landscape_size = (REMARKABLE_HEIGHT, REMARKABLE_WIDTH)
portrait_size = (REMARKABLE_WIDTH, REMARKABLE_HEIGHT)

class RemarkablePDFGenerator:
    """PDF generator optimized for reMarkable Pro device"""
    
    def __init__(self, filename: str):
        self.filename = filename
        self.canvas = canvas.Canvas(filename)
        self.canvas.setAuthor("reMarkable Calendar Exporter")
        self.canvas.setTitle("Weekly Calendar Overview - reMarkable Pro Optimized")
    
    def create_weekly_view_with_events(self, week_start_date: datetime.date, events: List[Dict]):
        """Create the landscape weekly overview page"""
        self.canvas.setPageSize(landscape_size)
        self.canvas.setFont("Helvetica-Bold", 36)
        self.canvas.drawString(inch, landscape_size[1] - inch, 
                              f"WEEKLY OVERVIEW - WEEK OF {week_start_date.strftime('%B %d, %Y').upper()}")
        
        # Draw weekly grid
        days = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
        x_start = inch
        y_start = landscape_size[1] - 2 * inch
        col_width = (landscape_size[0] - 2 * inch) / 8
        row_height = (landscape_size[1] - 4 * inch) / 31
        
        # Draw header with clickable day links
        self.canvas.setFont("Helvetica-Bold", 24)
        for i, day in enumerate(days):
            x_pos = x_start + (i + 1) * col_width + 20
            self.canvas.drawString(x_pos, y_start + 10, day)
            # Add clickable links to daily pages
            link_rect = (x_start + (i + 1) * col_width, y_start, 
                        x_start + (i + 2) * col_width, y_start + row_height)
            self.canvas.linkRect(day, f"day_{i+1}", link_rect)
        
        # Draw time slots (07:00-22:00 in military time)
        self.canvas.setFont("Helvetica", 18)
        for i in range(31):  # 31 half-hour slots from 07:00 to 22:00
            time = f"{(i // 2) + 7:02d}:{30 * (i % 2):02d}"
            self.canvas.drawString(x_start + 10, y_start - i * row_height, time)
        
        # Draw grid lines
        self.canvas.setStrokeColor(colors.black)
        self.canvas.setLineWidth(1)
        
        # Vertical lines
        for i in range(9):
            self.canvas.line(x_start + i * col_width, y_start + row_height, 
                           x_start + i * col_width, y_start - 30 * row_height)
        
        # Horizontal lines
        for i in range(32):
            self.canvas.line(x_start, y_start - (i-1) * row_height, 
                           x_start + 8 * col_width, y_start - (i-1) * row_height)
        
        # Add events to weekly view
        self.canvas.setFont("Helvetica", 12)
        for event in events:
            if not event.get('date'):
                continue
                
            try:
                event_date = datetime.datetime.strptime(event['date'], '%Y-%m-%d').date()
            except (ValueError, TypeError):
                continue
                
            day_offset = (event_date - week_start_date).days
            
            if 0 <= day_offset < 7:
                start_time_str = event.get('start_time', event.get('time', '09:00'))
                end_time_str = event.get('end_time', '')
                
                try:
                    start_time = datetime.datetime.strptime(start_time_str, '%H:%M').time()
                except (ValueError, TypeError):
                    start_time = datetime.time(9, 0)
                
                if not end_time_str:
                    duration = event.get('duration', 60)
                    end_hour = start_time.hour + (start_time.minute + duration) // 60
                    end_minute = (start_time.minute + duration) % 60
                    end_time = datetime.time(min(end_hour, 22), end_minute)
                else:
                    try:
                        end_time = datetime.datetime.strptime(end_time_str, '%H:%M').time()
                    except (ValueError, TypeError):
                        end_time = datetime.time(start_time.hour + 1, start_time.minute)
                
                start_hour = start_time.hour + start_time.minute / 60
                end_hour = end_time.hour + end_time.minute / 60
                
                if 7 <= start_hour <= 22:
                    start_row = int((start_hour - 7) * 2)
                    end_row = int((end_hour - 7) * 2)
                    
                    event_x = x_start + (day_offset + 1) * col_width + 5
                    event_y_start = y_start - start_row * row_height
                    event_height = max((end_row - start_row) * row_height, row_height)
                    
                    # Draw event block
                    self.canvas.setFillColor(colors.lightblue)
                    self.canvas.rect(event_x, event_y_start - event_height, col_width - 10, event_height, fill=1)
                    
                    # Add event text
                    self.canvas.setFillColor(colors.black)
                    title = event.get('title', event.get('summary', 'Untitled'))[:20]
                    self.canvas.drawString(event_x + 5, event_y_start - 15, title)
        
        self.canvas.showPage()
    
    def create_daily_view_with_events(self, date: datetime.date, day_name: str, 
                                     page_num: int, day_events: List[Dict]):
        """Create portrait daily view pages"""
        self.canvas.setPageSize(portrait_size)
        self.canvas.setFont("Helvetica-Bold", 36)
        self.canvas.drawString(inch, portrait_size[1] - inch, 
                              f"{day_name.upper()} - {date.strftime('%B %d, %Y')}")
        
        # Add link back to weekly view
        self.canvas.setFont("Helvetica", 18)
        self.canvas.drawString(inch, portrait_size[1] - 1.5*inch, "← Back to Weekly Overview")
        self.canvas.linkRect("← Back to Weekly", "weekly_view", 
                           (inch, portrait_size[1] - 1.5*inch, 3*inch, portrait_size[1] - inch))
        
        # Draw daily schedule
        x_start = inch
        y_start = portrait_size[1] - 2 * inch
        row_height = (portrait_size[1] - 4 * inch) / 31
        
        # Draw time slots
        self.canvas.setFont("Helvetica", 18)
        for i in range(31):
            time = f"{(i // 2) + 7:02d}:{30 * (i % 2):02d}"
            self.canvas.drawString(x_start + 10, y_start - i * row_height, time)
        
        # Draw grid lines
        self.canvas.setStrokeColor(colors.black)
        self.canvas.setLineWidth(1)
        self.canvas.line(x_start + 1.5*inch, y_start + row_height, 
                       x_start + 1.5*inch, y_start - 30 * row_height)
        
        for i in range(32):
            self.canvas.line(x_start, y_start - (i-1) * row_height, 
                           portrait_size[0] - inch, y_start - (i-1) * row_height)
        
        # Add events to daily view
        self.canvas.setFont("Helvetica", 14)
        for event in day_events:
            start_time_str = event.get('start_time', event.get('time', '09:00'))
            end_time_str = event.get('end_time', '')
            
            try:
                start_time = datetime.datetime.strptime(start_time_str, '%H:%M').time()
            except (ValueError, TypeError):
                start_time = datetime.time(9, 0)
            
            if not end_time_str:
                duration = event.get('duration', 60)
                end_hour = start_time.hour + (start_time.minute + duration) // 60
                end_minute = (start_time.minute + duration) % 60
                end_time = datetime.time(min(end_hour, 22), end_minute)
            else:
                try:
                    end_time = datetime.datetime.strptime(end_time_str, '%H:%M').time()
                except (ValueError, TypeError):
                    end_time = datetime.time(start_time.hour + 1, start_time.minute)
            
            start_hour = start_time.hour + start_time.minute / 60
            end_hour = end_time.hour + end_time.minute / 60
            
            if 7 <= start_hour <= 22:
                start_row = int((start_hour - 7) * 2)
                end_row = int((end_hour - 7) * 2)
                
                event_x = x_start + 1.5*inch + 10
                event_y_start = y_start - start_row * row_height
                event_height = max((end_row - start_row) * row_height, row_height)
                event_width = portrait_size[0] - x_start - 1.5*inch - 2*inch
                
                # Draw event block
                self.canvas.setFillColor(colors.lightblue)
                self.canvas.rect(event_x, event_y_start - event_height, event_width, event_height, fill=1)
                
                # Add event text
                self.canvas.setFillColor(colors.black)
                title = event.get('title', event.get('summary', 'Untitled'))
                self.canvas.drawString(event_x + 5, event_y_start - 20, title)
                
                description = event.get('description', event.get('location', ''))
                if description:
                    self.canvas.setFont("Helvetica", 12)
                    self.canvas.drawString(event_x + 5, event_y_start - 35, description[:50])
                    self.canvas.setFont("Helvetica", 14)
        
        self.canvas.showPage()
    
    def generate_calendar_pdf(self, week_start_date: datetime.date, events: List[Dict]):
        """Generate the complete PDF with weekly and daily views"""
        # Create weekly view with events
        self.canvas.bookmarkPage("weekly_view")
        self.canvas.addOutlineEntry("Weekly Overview", "weekly_view", 0, 0)
        self.create_weekly_view_with_events(week_start_date, events)
        
        # Create daily views with events
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for i, day in enumerate(days):
            date = week_start_date + datetime.timedelta(days=i)
            # Filter events for this specific day
            day_events = []
            for event in events:
                if event.get('date'):
                    try:
                        event_date = datetime.datetime.strptime(event['date'], '%Y-%m-%d').date()
                        if event_date == date:
                            day_events.append(event)
                    except (ValueError, TypeError):
                        continue
            
            self.canvas.bookmarkPage(f"day_{i+1}")
            self.canvas.addOutlineEntry(day, f"day_{i+1}", 1, 0)
            self.create_daily_view_with_events(date, day, i + 2, day_events)
        
        self.canvas.save()
        print(f"PDF generated successfully: {self.filename}")
        return self.filename

def transform_google_calendar_events(google_events: List[Dict]) -> List[Dict]:
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

def generate_pdf_from_week_data(week_data: Dict, start_date: str, output_filename: str = None) -> str:
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
        output_filename = f"remarkable_calendar_{week_start.strftime('%Y%m%d')}.pdf"
    
    # Create PDF generator and generate the PDF
    pdf_gen = RemarkablePDFGenerator(output_filename)
    pdf_gen.generate_calendar_pdf(week_start, all_events)
    
    return output_filename

if __name__ == "__main__":
    # Test the generator with sample data
    today = datetime.date.today()
    week_start = today - datetime.timedelta(days=today.weekday())
    
    sample_events = [
        {
            "title": "Team Meeting",
            "date": week_start.strftime('%Y-%m-%d'),
            "start_time": "09:00",
            "end_time": "10:30",
            "description": "Weekly team sync"
        },
        {
            "title": "Project Review",
            "date": (week_start + datetime.timedelta(days=2)).strftime('%Y-%m-%d'),
            "start_time": "14:00",
            "end_time": "15:30",
            "description": "Quarterly project review"
        }
    ]
    
    filename = f"test_remarkable_calendar_{week_start.strftime('%Y%m%d')}.pdf"
    pdf_gen = RemarkablePDFGenerator(filename)
    pdf_gen.generate_calendar_pdf(week_start, sample_events)