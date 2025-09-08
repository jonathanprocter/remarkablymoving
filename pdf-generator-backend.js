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
  }
  
  generateId() {
    return `event-${this.nextId++}`;
  }
  
  addEvent(event) {
    const eventId = this.generateId();
    event.id = eventId;
    this.events.set(eventId, event);
    
    // Add to weekly view if multi-day or important
    if (event.duration > 60 || event.priority === 'high' || event.showInWeekly) {
      this.weeklyEvents.add(eventId);
    }
    
    // Add to specific day
    const dateKey = event.dayKey || event.date.toLocaleDateString('en-US', { weekday: 'long' }).toLowerCase();
    if (!this.dailyEvents.has(dateKey)) {
      this.dailyEvents.set(dateKey, new Set());
    }
    this.dailyEvents.get(dateKey).add(eventId);
    
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
      width: '91mm',
      height: '163mm',
      printBackground: true,
      preferCSSPageSize: true,
      displayHeaderFooter: false,
      margin: { top: '0', right: '0', bottom: '0', left: '0' },
      scale: 1.0,
      pageRanges: '1-8'
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
    /* Device-specific measurements for reMarkable Paper Pro Move */
    :root {
      --device-width: 91mm;
      --device-height: 163mm;
      --usable-width: 85mm;
      --usable-height: 157mm;
      --base-font: 6pt;
      --small-font: 5pt;
      --tiny-font: 4pt;
    }
    
    /* Weekly Overview - Landscape */
    @page weekly {
      size: 163mm 91mm;
      margin: 3mm;
    }
    
    /* Daily Pages - Portrait */
    @page daily {
      size: 91mm 163mm;
      margin: 2mm;
    }
    
    @page {
      margin: 0;
      size: 91mm 163mm;  /* Portrait for daily pages - Pro Move dimensions */
    }
    
    /* Weekly page - landscape orientation for narrow screen */
    @page :first {
      size: 163mm 91mm;  /* Landscape for weekly overview - Pro Move dimensions */
    }
    
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }
    
    body {
      font-family: 'Courier New', 'Liberation Mono', monospace;
      font-size: var(--base-font);
      line-height: 1.1;
      color: #000;
      background: #fff;
    }
    
    /* Weekly Layout - Landscape for reMarkable Paper Pro Move (7.3" screen) */
    .weekly-page {
      width: 163mm;  /* Pro Move landscape width */
      height: 91mm;   /* Pro Move landscape height */
      padding: 3mm;   /* Minimal padding for small screen */
      page-break-after: always;
      display: grid;
      grid-template-rows: 15mm 1fr 20mm;
      gap: 1mm;
    }
    
    .weekly-header {
      text-align: center;
      border-bottom: 1pt solid #000;
      padding-bottom: 2mm;
      margin-bottom: 2mm;
    }
    
    .weekly-title {
      font-size: 10pt;  /* Reduced for small screen */
      font-weight: bold;
      letter-spacing: 0.5px;
    }
    
    .weekly-subtitle {
      font-size: 8pt;  /* Reduced for small screen */
      margin-top: 1mm;
    }
    
    .weekly-grid {
      display: grid;
      grid-template-columns: 20mm repeat(7, 1fr);
      grid-template-rows: 8mm repeat(8, 1fr); /* Reduced to 8 time slots for weekly view */
      gap: 0.5pt;
      border: 1pt solid #000;
    }
    
    .time-slot, .day-header, .grid-cell {
      border-right: 0.5pt solid #000;
      border-bottom: 0.5pt solid #000;
      padding: 0.5px 1px;
      font-size: 6pt;  /* Smaller for narrow screen */
      overflow: hidden;
    }
    
    .day-header {
      font-weight: bold;
      text-align: center;
      background: #000;
      color: #fff;
      padding: 1px;
      font-size: 7pt;  /* Smaller for narrow screen */
    }
    
    .time-slot {
      font-weight: bold;
      text-align: center;
      background: #f0f0f0;
      writing-mode: horizontal-tb;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    
    .grid-cell {
      position: relative;
      min-height: 5mm;  /* Reduced for small screen */
      vertical-align: top;
    }
    
    .weekly-event {
      background: #000;
      color: #fff;
      padding: 0.5px 1px;
      margin: 0.25px;
      font-size: 5pt;  /* Very small for narrow cells */
      border-radius: 0.5px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      line-height: 1;
      display: block;
      width: calc(100% - 2px);
    }
    
    .weekly-sidebar {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 3mm;
      padding: 2mm;
      font-size: var(--small-font);
    }
    
    .priority-tasks, .weekly-goals {
      border: 1pt solid #000;
      padding: 2mm;
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
    .daily-container {
      width: 87mm;
      height: 159mm;
      display: grid;
      grid-template-rows: 12mm 80mm 25mm 25mm 15mm;
      gap: 1mm;
      font-size: var(--base-font);
    }
    
    .daily-page {
      width: 91mm;   /* Pro Move portrait width */
      height: 163mm;  /* Pro Move portrait height */
      padding: 2mm;   /* Minimal padding for small screen */
      page-break-before: always;
      page-break-after: always;
      display: flex;
      flex-direction: column;
      margin: 0 auto;
      box-sizing: border-box;
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
      border-bottom: 1pt solid #000;
      padding-bottom: 1mm;
      margin-bottom: 2mm;
    }
    
    .daily-title {
      font-size: 8pt;  /* Smaller for Pro Move */
      font-weight: bold;
      letter-spacing: 0.3px;
    }
    
    .daily-subtitle {
      font-size: 6pt;  /* Smaller for Pro Move */
      margin-top: 1mm;
      color: #333;
    }
    
    /* Optimized time grid - CRITICAL FIX */
    .time-grid {
      display: grid;
      grid-template-columns: 16mm 1fr;
      grid-template-rows: repeat(16, 1fr); /* 16 slots instead of 30 */
      border: 1pt solid #000;
      font-size: var(--small-font);
    }
    
    .schedule-grid {
      display: grid;
      grid-template-columns: 16mm 1fr;  /* Narrower time column */
      grid-template-rows: repeat(16, 1fr); /* 16 hour slots */
      border: 1pt solid #000;
    }
    
    .time-label {
      border-right: 0.5pt solid #000;
      border-bottom: 0.5pt solid #000;
      padding: 0.5mm;
      font-size: 6pt;  /* Smaller for Pro Move */
      text-align: center;
      background: #f5f5f5;
      font-weight: bold;
    }
    
    .time-content {
      border-bottom: 0.5pt solid #ccc;
      padding: 0.5mm;
      min-height: 4.5mm;  /* Optimized for 16 slots */
      font-size: var(--tiny-font);
      position: relative;
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
      margin: 0.5mm 0;
      height: 2mm;
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
      border: 1pt solid #000;
      padding: 1mm;
      display: grid;
      grid-template-rows: 5mm repeat(3, 1fr);
    }
    
    .priority-header {
      font-weight: bold;
      border-bottom: 0.5pt solid #000;
      display: flex;
      align-items: center;
      font-size: var(--small-font);
    }
    
    .priority-item {
      display: flex;
      align-items: center;
      gap: 2mm;
      font-size: var(--small-font);
    }
    
    .priority-content {
      flex: 1;
      border-bottom: 0.5pt solid #ccc;
      min-height: 3mm;
    }
    
    /* Goals and Notes */
    .daily-goals, .notes {
      border: 1pt solid #000;
      padding: 1mm;
      font-size: var(--small-font);
    }
    
    .goal-header, .notes-header {
      font-weight: bold;
      font-size: var(--small-font);
      border-bottom: 0.5pt solid #000;
      padding-bottom: 0.5mm;
      margin-bottom: 1mm;
    }
    
    .goal-content, .notes-content {
      min-height: 15mm;
      font-size: var(--tiny-font);
    }
    
    .status {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: var(--tiny-font);
      color: #666;
      padding: 1mm;
      border-top: 0.5pt solid #ccc;
    }
    
    .event-count, .sync-status {
      font-size: var(--tiny-font);
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
  const timeSlots = generateTimeSlots(9, 16, 60); // 9 AM to 5 PM for weekly view, hourly only
  
  return `
    <div class="weekly-page">
        <div class="weekly-header">
            <div class="weekly-title">WEEKLY PLANNER</div>
            <div class="weekly-subtitle">WEEK OF ${weekDays[0].date}</div>
        </div>
        
        <div class="weekly-grid">
            <div class="time-slot">TIME</div>
            ${weekDays.map(day => `<div class="day-header">${day.name.substring(0, 3)}</div>`).join('')}
            
            ${timeSlots.map(time => `
                <div class="time-slot">${time}</div>
                ${weekDays.map(day => `
                    <div class="grid-cell">
                        ${getWeeklyEventsForTimeSlot(weekData, day.key, time)}
                    </div>
                `).join('')}
            `).join('')}
        </div>
        
        <div class="weekly-sidebar">
            <div class="priority-tasks">
                <h3>PRIORITY TASKS</h3>
                ${(weekData.priorityTasks || []).slice(0, 5).map(task => 
                    `<div class="checkbox-item"><div class="checkbox"></div>${task}</div>`
                ).join('')}
                ${Array(Math.max(0, 5 - (weekData.priorityTasks || []).length)).fill().map(() => 
                    `<div class="checkbox-item"><div class="checkbox"></div><div class="goal-line" style="flex: 1;"></div></div>`
                ).join('')}
            </div>
            <div class="weekly-goals">
                <h3>WEEKLY GOALS</h3>
                ${(weekData.weeklyGoals || []).slice(0, 3).map(goal => 
                    `<div style="margin: 0.5mm 0; font-size: 6pt;">${goal}</div>`
                ).join('')}
                ${Array(Math.max(0, 4 - (weekData.weeklyGoals || []).length)).fill().map(() => '<div class="goal-line"></div>').join('')}
        </div>
    </div>`;
}

function generateDailyPages(weekData, weekDays, eventManager) {
  return weekDays.map(day => generateDailyPage(weekData, day, eventManager)).join('');
}

function generateDailyPage(weekData, day, eventManager) {
  const timeSlots = generateTimeSlots(7, 22, 60); // 7 AM to 10 PM, HOURLY intervals (16 slots)
  const dayEvents = eventManager ? eventManager.getDailyEvents(day.key) : (weekData.events?.[day.key] || []);
  
  return `
    <div class="daily-page" data-date="${day.dateObj.toISOString().split('T')[0]}">
        <div class="daily-container">
            <div class="daily-header">
                <span class="daily-title">DAILY PLANNER - ${day.name}</span>
                <span class="daily-subtitle">${day.date}</span>
            </div>
            
            <div class="time-grid">
                ${timeSlots.map(time => `
                    <div class="time-label">${time}</div>
                    <div class="time-content" data-time="${time}">
                        ${getDailyEventsForTime(dayEvents, time)}
                    </div>
                `).join('')}
            </div>
            
            <div class="priorities">
                <div class="priority-header">PRIORITIES</div>
                <div class="priority-item">A) <span class="priority-content"></span></div>
                <div class="priority-item">B) <span class="priority-content"></span></div>
                <div class="priority-item">C) <span class="priority-content"></span></div>
            </div>
            
            <div class="daily-goals">
                <div class="goal-header">DAILY GOALS</div>
                <div class="goal-content"></div>
            </div>
            
            <div class="notes">
                <div class="notes-header">NOTES</div>
                <div class="notes-content"></div>
            </div>
            
            <div class="status">
                <span class="event-count">${dayEvents.length} events scheduled</span>
                <span class="sync-status">${getTotalEventCount(weekData)} total synced</span>
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
      
      // Show event if it overlaps with this hour slot
      return (eventStartTime < slotEndTime && eventEndTime > slotTime);
    })
    .map(event => {
      const truncatedTitle = event.title.substring(0, 10) + (event.title.length > 10 ? '...' : '');
      const bgColor = event.priority === 'high' ? '#ffcccc' : '#f0f0f0';
      return `<div class="weekly-event" style="background-color: ${bgColor}; color: #000;">${truncatedTitle}</div>`;
    })
    .join('');
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
      const bgColor = event.priority === 'high' ? '#ffcccc' : 'transparent';
      return `<div class="daily-event" style="background-color: ${bgColor};">${event.title}</div>`;
    })
    .join('');
}

function getTotalEventCount(weekData) {
  if (!weekData.events) return 0;
  return Object.values(weekData.events).reduce((total, dayEvents) => total + dayEvents.length, 0);
}

module.exports = router;