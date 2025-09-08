// pdf-generator-backend.js - Express backend for PDF generation
const express = require('express');
const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs').promises;

const router = express.Router();

// Event management system for bidirectional linking
class PlannerEventManager {
  constructor() {
    this.events = new Map(); // eventId -> event object
    this.weeklyEvents = new Set(); // events visible on weekly view
    this.dailyEvents = new Map(); // date -> Set of eventIds
    this.nextId = 1;
    this.eventCounter = 0;
    this.weeklyTotal = 0;
    this.dailyCounts = {
      mon: 0, tue: 0, wed: 0, thu: 0, 
      fri: 0, sat: 0, sun: 0
    };
  }
  
  generateId() {
    return `event-${this.nextId++}`;
  }
  
  addEvent(event) {
    const eventId = this.generateId();
    event.id = eventId;
    this.events.set(eventId, event);
    
    // Add to weekly view if multi-day or important or within business hours
    const [eventHour] = (event.time || '09:00').split(':').map(Number);
    const isBusinessHour = eventHour >= 9 && eventHour <= 17;
    
    if ((event.duration > 60 || event.priority === 'high' || event.showInWeekly) && isBusinessHour) {
      this.weeklyEvents.add(eventId);
    }
    
    // Add to specific day
    const dateKey = event.dayKey || event.date.toLocaleDateString('en-US', { weekday: 'long' }).toLowerCase();
    if (!this.dailyEvents.has(dateKey)) {
      this.dailyEvents.set(dateKey, new Set());
    }
    this.dailyEvents.get(dateKey).add(eventId);
    
    // Update counts
    const dayAbbr = dateKey.substring(0, 3);
    if (this.dailyCounts[dayAbbr] !== undefined) {
      this.dailyCounts[dayAbbr]++;
      this.weeklyTotal++;
    }
    
    return eventId;
  }
  
  getWeeklyEvents() {
    return Array.from(this.weeklyEvents).map(id => this.events.get(id));
  }
  
  getDailyEvents(dayKey) {
    const eventIds = this.dailyEvents.get(dayKey) || new Set();
    return Array.from(eventIds).map(id => this.events.get(id));
  }
  
  getAllEvents() {
    return Array.from(this.events.values());
  }
  
  isBusinessHour(time) {
    const hour = parseInt(time.split(':')[0]);
    return hour >= 9 && hour <= 17;
  }
}

// PDF generation endpoint
router.post('/generate-planner-pdf', async (req, res) => {
  try {
    const { weekData, startDate } = req.body;
    
    // Generate HTML content
    const htmlContent = generatePlannerHTML(weekData, startDate);
    
    // Launch puppeteer with system chromium
    const browser = await puppeteer.launch({
      headless: true,
      executablePath: process.env.PUPPETEER_EXECUTABLE_PATH || '/nix/store/qa9cnw4v5xkxyip6mb9kxqfq1z4x2dx1-chromium-138.0.7204.100/bin/chromium',
      args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
    });
    
    const page = await browser.newPage();
    
    // Set content
    await page.setContent(htmlContent, { waitUntil: 'networkidle0' });
    
    // Generate PDF with reMarkable Pro Move dimensions
    // Optimized for 7.3" screen (91mm × 163mm)
    const pdf = await page.pdf({
      printBackground: true,
      preferCSSPageSize: true,  // Let CSS control page sizes
      displayHeaderFooter: false,
      margin: { top: '0', right: '0', bottom: '0', left: '0' }
    });
    
    await browser.close();
    
    // Set headers for file download
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', `attachment; filename="planner-${startDate}.pdf"`);
    
    res.send(pdf);
  } catch (error) {
    console.error('PDF generation error:', error);
    res.status(500).json({ error: 'Failed to generate PDF' });
  }
});

// HTML template generator with event manager
function generatePlannerHTML(weekData, startDate) {
  const date = new Date(startDate);
  const weekDays = [];
  const eventManager = new PlannerEventManager();
  
  // Generate week days
  for (let i = 0; i < 7; i++) {
    const currentDate = new Date(date);
    currentDate.setDate(date.getDate() + i);
    weekDays.push({
      name: currentDate.toLocaleDateString('en-US', { weekday: 'long' }).toUpperCase(),
      date: currentDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }).toUpperCase(),
      key: currentDate.toLocaleDateString('en-US', { weekday: 'long' }).toLowerCase(),
      dateObj: currentDate
    });
  }
  
  // Process and add events to manager for bidirectional linking
  if (weekData.events) {
    Object.keys(weekData.events).forEach(dayKey => {
      const dayEvents = weekData.events[dayKey] || [];
      dayEvents.forEach(event => {
        eventManager.addEvent({
          ...event,
          dayKey,
          date: new Date(),
          priority: event.priority || (event.duration > 90 ? 'high' : 'normal'),
          showInWeekly: event.duration > 60 || event.priority === 'high'
        });
      });
    });
  }
  
  return `<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>reMarkable Planner</title>
    <style>
        ${getOptimizedCSS()}
    </style>
</head>
<body>
    ${generateWeeklyPage(weekData, weekDays, eventManager)}
    ${generateDailyPages(weekData, weekDays, eventManager)}
</body>
</html>`;
}

function getOptimizedCSS() {
  return `
    /* Device specifications for reMarkable Paper Pro Move */
    :root {
      --device-width-portrait: 91mm;
      --device-height-portrait: 163mm;
      --device-width-landscape: 163mm;
      --device-height-landscape: 91mm;
      --margin: 2mm;
      --usable-width-portrait: 87mm;
      --usable-height-portrait: 159mm;
      --usable-width-landscape: 159mm;
      --usable-height-landscape: 87mm;
      
      /* Typography */
      --font-large: 8pt;
      --font-medium: 6pt;
      --font-small: 5pt;
      --font-tiny: 4pt;
    }
    
    /* Page sizing for reMarkable Paper Pro Move */
    @page {
      margin: var(--margin);
    }
    
    /* First page (weekly) - landscape */
    @page :first {
      size: 163mm 91mm;
      margin: var(--margin);
    }
    
    /* Daily pages - Portrait */
    @page :not(:first) {
      size: 91mm 163mm;
      margin: var(--margin);
    }
    
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }
    
    h1, h2, h3 {
      margin: 0;
      padding: 0;
    }
    
    body {
      font-family: 'Times', serif;
      color: #000000;
      background: #ffffff;
      -webkit-print-color-adjust: exact;
    }
    
    /* Page structure */
    .page {
      page-break-after: always;
      page-break-inside: avoid;
    }
    
    .page:last-child {
      page-break-after: auto;
    }
    
    /* Weekly Layout - Landscape for reMarkable Paper Pro Move (7.3" screen) */
    .weekly-page {
      width: var(--usable-width-landscape);
      height: var(--usable-height-landscape);
    }
    
    .weekly-container {
      width: 100%;
      height: 100%;
      display: flex;
      flex-direction: column;
    }
    
    .weekly-header {
      height: 12mm;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1pt solid #000;
      padding: 0 2mm;
      margin-bottom: 2mm;
    }
    
    .weekly-header h1 {
      font-size: var(--font-large);
      font-weight: bold;
    }
    
    .weekly-header span {
      font-size: var(--font-medium);
    }
    
    .weekly-main {
      flex: 1;
      display: flex;
      gap: 3mm;
    }
    
    .weekly-grid {
      flex: 2;
      display: grid;
      grid-template-columns: 15mm repeat(7, 1fr);
      grid-template-rows: 8mm repeat(9, 1fr); /* 09:00-17:00 business hours */
      gap: 0.5pt;
      border: 1pt solid #000;
      font-size: var(--font-small);
    }
    
    .time-header, .day-header {
      background: #f0f0f0;
      font-weight: bold;
      display: flex;
      align-items: center;
      justify-content: center;
      border-right: 0.5pt solid #000;
      border-bottom: 0.5pt solid #000;
      font-size: var(--font-small);
    }
    
    .time-label {
      background: #f8f8f8;
      font-weight: bold;
      display: flex;
      align-items: center;
      justify-content: center;
      border-right: 0.5pt solid #000;
      border-bottom: 0.5pt solid #ccc;
      font-size: var(--font-tiny);
    }
    
    .event-cell {
      border-right: 0.5pt solid #ccc;
      border-bottom: 0.5pt solid #ccc;
      padding: 0.5mm;
      font-size: var(--font-tiny);
      overflow: hidden;
    }
    
    .weekly-sidebar {
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 2mm;
    }
    
    .priority-section, .goals-section {
      border: 1pt solid #000;
      padding: 2mm;
      flex: 1;
    }
    
    .priority-section h3, .goals-section h3 {
      font-size: var(--font-medium);
      font-weight: bold;
      margin-bottom: 1mm;
      border-bottom: 0.5pt solid #000;
      padding-bottom: 0.5mm;
    }
    
    .task-item, .goal-item {
      font-size: var(--font-small);
      margin-bottom: 0.5mm;
      line-height: 1.2;
    }
    
    /* Remove old footer styles */
    .weekly-footer, .footer-section, .footer-title,
    .checkbox-item, .checkbox {
      display: none;
    }
    
    .weekly-footer {
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      gap: 2mm;
      margin-top: 2mm;
      height: 15mm;
    }
    
    .footer-section {
      border: 1pt solid #000;
      padding: 1mm;
      font-size: 5pt;
    }
    
    .footer-title {
      font-weight: bold;
      font-size: 6pt;
      border-bottom: 0.5pt solid #000;
      margin-bottom: 1mm;
    }
    
    .footer-section {
      border: 0.5pt solid #000;
      padding: 1mm;
    }
    
    .footer-title {
      font-weight: bold;
      font-size: 7pt;  /* Smaller for Pro Move */
      border-bottom: 0.5pt solid #000;
      padding-bottom: 1mm;
      margin-bottom: 1mm;
      text-align: center;
    }
    
    .checkbox-item {
      display: flex;
      align-items: center;
      margin: 0.75mm 0;
      font-size: 6pt;  /* Smaller for Pro Move */
    }
    
    .checkbox {
      width: 2mm;
      height: 2mm;
      border: 0.5pt solid #000;
      margin-right: 1mm;
      flex-shrink: 0;
      background: #fff;
    }
    
    /* Daily Layout - Portrait for reMarkable Paper Pro Move (7.3" screen) */
    .daily-page {
      width: var(--usable-width-portrait);
      height: var(--usable-height-portrait);
    }
    
    .daily-container {
      flex: 1;
      display: flex;
      flex-direction: column;
    }
    
    .daily-main {
      flex: 1;
      margin-right: 2mm;
    }
    
    .daily-sidebar {
      width: 25mm;  /* Narrower sidebar for small screen */
      border-left: 0.5pt solid #000;
      padding-left: 1mm;
    }
    
    .daily-header {
      height: 10mm;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1pt solid #000;
      padding: 0 1mm;
      margin-bottom: 1mm;
    }
    
    .daily-title {
      font-size: var(--font-medium);
      font-weight: bold;
    }
    
    .daily-date {
      font-size: var(--font-small);
    }
    
    /* Time grid for daily pages */
    .time-grid {
      flex: 1;
      border: 1pt solid #000;
      display: flex;
      flex-direction: column;
    }
    
    .time-row {
      flex: 1;
      display: flex;
      border-bottom: 0.5pt solid #ccc;
    }
    
    .time-row:last-child {
      border-bottom: none;
    }
    
    .time-row .time-label {
      width: 12mm;
      background: #f8f8f8;
      font-weight: bold;
      display: flex;
      align-items: center;
      justify-content: center;
      border-right: 1pt solid #000;
      font-size: var(--font-tiny);
    }
    
    .time-content {
      flex: 1;
      padding: 0.5mm;
      font-size: var(--font-small);
      min-height: 8mm;
    }
    
    .daily-bottom {
      height: 35mm;
      margin-top: 1mm;
      display: grid;
      grid-template-columns: 1fr 1fr;
      grid-template-rows: 15mm 10mm 8mm;
      gap: 1mm;
    }
    
    .daily-event {
      background: #000;
      color: #fff;
      padding: 0.5mm 1mm;
      margin: 0.25mm 0;
      border-radius: 0.5px;
      font-size: 6pt;  /* Smaller for Pro Move */
      line-height: 1;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    
    .sidebar-section {
      border: 0.5pt solid #000;
      margin-bottom: 2mm;
      padding: 1mm;
    }
    
    .sidebar-title {
      font-weight: bold;
      font-size: 6pt;  /* Smaller for Pro Move */
      border-bottom: 0.5pt solid #000;
      padding-bottom: 0.5mm;
      margin-bottom: 1mm;
      text-align: center;
    }
    
    .goal-line {
      border-bottom: 0.5pt solid #ccc;
      margin: 1mm 0;
      height: 3mm;
    }
    
    .event-summary {
      font-size: 5pt;  /* Smaller for Pro Move */
      line-height: 1.1;
      margin: 0.5mm 0;
    }
    
    .status-text {
      font-size: 6pt;  /* Smaller for Pro Move */
      margin: 0.5mm 0;
    }
    
    /* Priority section for daily pages */
    .priorities {
      grid-column: 1 / 3;
      border: 1pt solid #000;
      padding: 1mm;
    }
    
    .section-header {
      font-size: var(--font-small);
      font-weight: bold;
      margin-bottom: 1mm;
    }
    
    .priority-line {
      font-size: var(--font-small);
      margin-bottom: 0.5mm;
      display: flex;
      align-items: center;
    }
    
    .fill-line {
      flex: 1;
      border-bottom: 0.5pt solid #ccc;
      margin-left: 2mm;
      height: 1px;
    }
    
    /* Goals and Notes */
    .daily-goals, .notes {
      border: 1pt solid #000;
      padding: 1mm;
    }
    
    .goals-content, .notes-content {
      font-size: var(--font-small);
      height: calc(100% - 6mm);
    }
    
    .status {
      grid-column: 1 / 3;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: var(--font-tiny);
      color: #666;
      padding: 0 1mm;
    }
    
    /* High contrast mode for better e-ink visibility */
    .high-contrast {
      filter: contrast(1.2);
    }
    
    /* Ensure proper page breaks */
    .page-break {
      page-break-before: always;
    }
  `;
}

function generateWeeklyPage(weekData, weekDays, eventManager) {
  const timeSlots = generateTimeSlots(9, 17, 60); // 9 AM to 5 PM business hours (9 slots)
  
  return `
    <div class="page weekly-page">
        <div class="weekly-container">
            <div class="weekly-header">
                <h1>WEEKLY PLANNER</h1>
                <span>WEEK OF ${weekDays[0].date}</span>
            </div>
            
            <div class="weekly-main">
                <div class="weekly-grid">
                    <div class="time-header">TIME</div>
                    ${weekDays.map(day => `<div class="day-header">${day.name.substring(0, 3).toUpperCase()}</div>`).join('')}
                    
                    ${timeSlots.map(time => {
                      const timeStr = time.replace(':', '');
                      return `
                        <div class="time-label">${time}</div>
                        ${weekDays.map(day => `
                            <div class="event-cell" id="w-${day.key.substring(0, 3)}-${timeStr}" data-day="${day.key.substring(0, 3)}" data-time="${time}">
                                ${getWeeklyEventsForTimeSlot(weekData, day.key, time)}
                            </div>
                        `).join('')}
                      `;
                    }).join('')}
                </div>
                
                <div class="weekly-sidebar">
                    <div class="priority-section">
                        <h3>PRIORITY TASKS</h3>
                        ${(weekData.priorityTasks || ['Follow up on client contracts', 'Prepare quarterly review materials', 'Update team schedules', 'Review project deliverables', 'Schedule follow-up meetings']).slice(0, 5).map((task, i) => 
                            `<div class="task-item" id="task-${i+1}">${task}</div>`
                        ).join('')}
                    </div>
                    
                    <div class="goals-section">
                        <h3>WEEKLY GOALS</h3>
                        ${(weekData.weeklyGoals || ['Complete all scheduled appointments', 'Review and update project timelines', 'Prepare for upcoming presentations']).slice(0, 3).map(goal => 
                            `<div class="goal-item">${goal}</div>`
                        ).join('')}
                    </div>
                </div>
            </div>
        </div>
    </div>`;
}

function generateDailyPages(weekData, weekDays, eventManager) {
  return weekDays.map(day => generateDailyPage(weekData, day, eventManager)).join('');
}

function generateDailyPage(weekData, day, eventManager) {
  const timeSlots = generateTimeSlots(7, 22, 60); // 7 AM to 10 PM, hourly intervals (16 slots)
  const dayEvents = eventManager ? eventManager.getDailyEvents(day.key) : (weekData.events?.[day.key] || []);
  const dayAbbr = day.key.substring(0, 3);
  
  return `
    <div class="page daily-page" data-date="${day.dateObj.toISOString().split('T')[0]}" data-day="${dayAbbr}">
        <div class="daily-container">
            <div class="daily-header">
                <span class="daily-title">DAILY PLANNER - ${day.name}</span>
                <span class="daily-date">${day.date}</span>
            </div>
            
            <div class="time-grid">
                ${timeSlots.map(time => {
                  const timeStr = time.replace(':', '');
                  return `
                    <div class="time-row">
                        <div class="time-label">${time}</div>
                        <div class="time-content" id="d-${dayAbbr}-${timeStr}" data-time="${time}" data-day="${dayAbbr}">
                            ${getDailyEventsForTime(dayEvents, time)}
                        </div>
                    </div>
                  `;
                }).join('')}
            </div>
            
            <div class="daily-bottom">
                <div class="priorities">
                    <div class="section-header">PRIORITIES</div>
                    <div class="priority-line">A) <span class="fill-line"></span></div>
                    <div class="priority-line">B) <span class="fill-line"></span></div>
                    <div class="priority-line">C) <span class="fill-line"></span></div>
                </div>
                
                <div class="daily-goals">
                    <div class="section-header">DAILY GOALS</div>
                    <div class="goals-content"></div>
                </div>
                
                <div class="notes">
                    <div class="section-header">NOTES</div>
                    <div class="notes-content"></div>
                </div>
                
                <div class="status">
                    <span id="event-count-${dayAbbr}">${dayEvents.length} events</span>
                    <span>Week: <span id="week-total">${getTotalEventCount(weekData)}</span> total</span>
                </div>
            </div>
        </div>
    </div>`;
}

// Utility functions
function generateTimeSlots(startHour, endHour, intervalMinutes) {
  const slots = [];
  for (let hour = startHour; hour <= endHour; hour++) {
    for (let minute = 0; minute < 60; minute += intervalMinutes) {
      if (hour === endHour && minute > 0) break;
      slots.push(`${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`);
    }
  }
  return slots;
}

function getWeeklyEventsForTimeSlot(weekData, dayKey, timeSlot) {
  const dayEvents = weekData.events?.[dayKey] || [];
  const [hour, minute] = timeSlot.split(':').map(Number);
  const slotTime = hour * 60 + minute;
  const slotEndTime = slotTime + 60; // Full hour slot
  
  return dayEvents
    .filter(event => {
      const [eventHour, eventMinute] = (event.time || '09:00').split(':').map(Number);
      const eventStartTime = eventHour * 60 + eventMinute;
      const eventEndTime = eventStartTime + (event.duration || 60);
      
      // Show event if it overlaps with this hour slot and is within business hours
      return (eventStartTime < slotEndTime && eventEndTime > slotTime) && 
             (eventHour >= 9 && eventHour <= 17);
    })
    .map(event => {
      const truncatedTitle = event.title.length > 8 ? event.title.substring(0, 8) + '...' : event.title;
      const bgColor = event.priority === 'high' ? '#e0e0e0' : '';
      return truncatedTitle ? `<span style="background-color: ${bgColor};">${truncatedTitle}</span>` : '';
    })
    .join(' ');
}

function getDailyEventsForTime(events, timeSlot) {
  const [hour, minute] = timeSlot.split(':').map(Number);
  const slotTime = hour * 60 + minute;
  const slotEndTime = slotTime + 60; // Hour slot
  
  return events
    .filter(event => {
      const [eventHour, eventMinute] = (event.time || '09:00').split(':').map(Number);
      const eventStartTime = eventHour * 60 + eventMinute;
      const eventEndTime = eventStartTime + (event.duration || 60);
      // Show events that start in or overlap with this hour
      return (eventStartTime >= slotTime && eventStartTime < slotEndTime) ||
             (eventStartTime < slotTime && eventEndTime > slotTime);
    })
    .map(event => {
      const bgColor = event.priority === 'high' ? '#f0f0f0' : '';
      return event.title ? `<span style="background-color: ${bgColor};">${event.title}</span>` : '';
    })
    .join(' ');
}

function getTotalEventCount(weekData) {
  if (!weekData.events) return 0;
  return Object.values(weekData.events).reduce((total, dayEvents) => total + dayEvents.length, 0);
}

module.exports = router;