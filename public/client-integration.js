// client-integration.js - Integration with your existing Replit calendar app

class RemarkablePDFGenerator {
  constructor(calendarData) {
    this.calendarData = calendarData;
    this.apiBaseURL = window.location.port === '5000' ? 'http://localhost:3001/api' : '/api';
  }

  // Convert your existing calendar data to the PDF generator format
  transformCalendarData(weekStartDate) {
    const weekData = {
      weekOf: weekStartDate,
      weeklyGoals: this.getWeeklyGoals(),
      priorityTasks: this.getPriorityTasks(),
      events: this.getWeekEvents(weekStartDate)
    };
    
    return weekData;
  }

  // Extract weekly goals from your calendar system
  getWeeklyGoals() {
    // This can be customized based on your data structure
    return [
      'Complete all scheduled appointments',
      'Review and update project timelines',
      'Prepare for upcoming presentations'
    ];
  }

  // Extract priority tasks
  getPriorityTasks() {
    // This can be customized based on your data structure
    return [
      'Follow up on client contracts',
      'Prepare quarterly review materials',
      'Update team schedules',
      'Review project deliverables',
      'Schedule follow-up meetings'
    ];
  }

  // Convert your calendar events to the required format
  getWeekEvents(weekStartDate) {
    const startDate = new Date(weekStartDate);
    const events = {
      monday: [],
      tuesday: [],
      wednesday: [],
      thursday: [],
      friday: [],
      saturday: [],
      sunday: []
    };
    
    const dayNames = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];
    
    this.calendarData.forEach(event => {
      const eventDate = new Date(event.date);
      const dayOfWeek = eventDate.getDay();
      const dayKey = dayNames[dayOfWeek];
      
      // Check if event falls within the week
      const weekEnd = new Date(startDate);
      weekEnd.setDate(startDate.getDate() + 6);
      
      if (eventDate >= startDate && eventDate <= weekEnd) {
        events[dayKey].push({
          time: event.time || '09:00',
          duration: event.duration || 60,
          title: event.title || event.summary || 'Untitled Event',
          type: event.type || 'appointment'
        });
      }
    });
    
    // Sort events by time for each day
    Object.keys(events).forEach(day => {
      events[day].sort((a, b) => {
        const timeA = a.time.split(':').reduce((h, m) => h * 60 + parseInt(m), 0);
        const timeB = b.time.split(':').reduce((h, m) => h * 60 + parseInt(m), 0);
        return timeA - timeB;
      });
    });
    
    return events;
  }

  // Generate and download the PDF
  async generatePDF(weekStartDate, options = {}) {
    try {
      // Show loading state
      this.showLoadingState();
      
      // Transform your calendar data
      const weekData = this.transformCalendarData(weekStartDate);
      
      // Prepare request data
      const requestData = {
        weekData: weekData,
        startDate: weekStartDate,
        options: {
          includeWeeklyOverview: options.includeWeeklyOverview !== false,
          includeDailyPages: options.includeDailyPages !== false,
          optimizeForRemarkable: options.optimizeForRemarkable !== false,
          ...options
        }
      };
      
      // Make API request
      const response = await fetch(`${this.apiBaseURL}/generate-planner-pdf`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
      });
      
      if (!response.ok) {
        throw new Error(`PDF generation failed: ${response.statusText}`);
      }
      
      // Get the PDF blob
      const pdfBlob = await response.blob();
      
      // Download the PDF
      this.downloadPDF(pdfBlob, weekStartDate);
      
      // Hide loading state
      this.hideLoadingState();
      
      return true;
    } catch (error) {
      console.error('Error generating PDF:', error);
      this.hideLoadingState();
      this.showError('Failed to generate PDF. Please try again.');
      return false;
    }
  }

  // Download the generated PDF
  downloadPDF(pdfBlob, weekStartDate) {
    const url = window.URL.createObjectURL(pdfBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `remarkable-planner-${weekStartDate}.pdf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }

  // UI helper methods
  showLoadingState() {
    const button = document.getElementById('generate-remarkable-pdf-btn');
    if (button) {
      button.disabled = true;
      button.innerHTML = '<span class="spinner"></span> Generating reMarkable PDF…';
    }
  }

  hideLoadingState() {
    const button = document.getElementById('generate-remarkable-pdf-btn');
    if (button) {
      button.disabled = false;
      button.innerHTML = '📱 Generate reMarkable PDF';
    }
  }

  showError(message) {
    const notification = document.createElement('div');
    notification.className = 'error-notification';
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: #f44336;
      color: white;
      padding: 15px;
      border-radius: 5px;
      z-index: 1000;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
      document.body.removeChild(notification);
    }, 5000);
  }
}

// Integration with your existing calendar application
class CalendarPDFIntegration {
  constructor() {
    this.pdfGenerator = null;
    this.currentWeekStart = this.getMonday(new Date());
  }

  // Initialize with your calendar data
  initialize(calendarData) {
    this.pdfGenerator = new RemarkablePDFGenerator(calendarData);
    this.setupUI();
  }

  // Get Monday of the current week
  getMonday(date) {
    const d = new Date(date);
    const day = d.getDay();
    const diff = d.getDate() - day + (day === 0 ? -6 : 1);
    return new Date(d.setDate(diff));
  }

  // Generate PDF directly from Google Calendar
  async generateFromCalendar(weekStartDate) {
    try {
      // Show loading state
      this.showLoadingState('generate-from-calendar-btn');
      
      // Get selected calendar IDs from the UI if available
      const selectedCalendars = this.getSelectedCalendars();
      
      // Prepare request data
      const requestData = {
        weekStart: weekStartDate || this.currentWeekStart.toISOString(),
        calendarIds: selectedCalendars
      };
      
      // Make API request to the new endpoint
      const response = await fetch('/api/generate-calendar-pdf', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
      });
      
      if (!response.ok) {
        throw new Error(`PDF generation failed: ${response.statusText}`);
      }
      
      // Get the PDF blob
      const pdfBlob = await response.blob();
      
      // Download the PDF
      const dateStr = new Date(weekStartDate || this.currentWeekStart).toISOString().split('T')[0];
      this.downloadPDF(pdfBlob, dateStr);
      
      // Hide loading state
      this.hideLoadingState('generate-from-calendar-btn');
      
      // Show success message
      this.showSuccess('reMarkable Pro PDF generated successfully!');
      
      return true;
    } catch (error) {
      console.error('Error generating PDF from calendar:', error);
      this.hideLoadingState('generate-from-calendar-btn');
      this.showError('Failed to generate PDF. Please make sure you are authenticated.');
      return false;
    }
  }
  
  // Get selected calendars from the UI
  getSelectedCalendars() {
    const checkboxes = document.querySelectorAll('input[name="calendar-selection"]:checked');
    return Array.from(checkboxes).map(cb => cb.value);
  }
  
  // Download the generated PDF
  downloadPDF(pdfBlob, dateStr) {
    const url = window.URL.createObjectURL(pdfBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `remarkable-calendar-${dateStr}.pdf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }
  
  // UI helper methods
  showLoadingState(buttonId) {
    const button = document.getElementById(buttonId);
    if (button) {
      button.disabled = true;
      button.innerHTML = '<span class="spinner"></span> Generating PDF...';
    }
  }
  
  hideLoadingState(buttonId) {
    const button = document.getElementById(buttonId);
    if (button) {
      button.disabled = false;
      if (buttonId === 'generate-from-calendar-btn') {
        button.innerHTML = '📅 Generate from Google Calendar';
      } else {
        button.innerHTML = '📱 Generate reMarkable PDF';
      }
    }
  }
  
  showSuccess(message) {
    const notification = document.createElement('div');
    notification.className = 'success-notification';
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: #4CAF50;
      color: white;
      padding: 15px;
      border-radius: 5px;
      z-index: 1000;
      box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    `;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
      notification.style.opacity = '0';
      setTimeout(() => {
        document.body.removeChild(notification);
      }, 300);
    }, 3000);
  }
  
  showError(message) {
    const notification = document.createElement('div');
    notification.className = 'error-notification';
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: #f44336;
      color: white;
      padding: 15px;
      border-radius: 5px;
      z-index: 1000;
      box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    `;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
      notification.style.opacity = '0';
      setTimeout(() => {
        document.body.removeChild(notification);
      }, 300);
    }, 5000);
  }

  // Setup the PDF generation UI
  setupUI() {
    // Check if UI already exists
    if (document.getElementById('remarkable-pdf-controls')) {
      return;
    }

    // Create container for PDF controls
    const controlContainer = document.createElement('div');
    controlContainer.id = 'remarkable-pdf-controls';
    controlContainer.className = 'pdf-controls';
    controlContainer.style.cssText = `
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 10px;
      background: #f5f5f5;
      border-radius: 8px;
      margin: 10px 0;
    `;

    // Add week selector
    const weekSelector = document.createElement('input');
    weekSelector.type = 'date';
    weekSelector.id = 'remarkable-week-selector';
    weekSelector.value = this.currentWeekStart.toISOString().split('T')[0];
    weekSelector.style.cssText = `
      padding: 8px;
      border: 1px solid #ddd;
      border-radius: 4px;
    `;
    weekSelector.onchange = (e) => {
      this.currentWeekStart = this.getMonday(new Date(e.target.value));
    };

    // Add PDF generation button
    const pdfButton = document.createElement('button');
    pdfButton.id = 'generate-remarkable-pdf-btn';
    pdfButton.className = 'pdf-generate-btn';
    pdfButton.innerHTML = '📱 Generate reMarkable PDF';
    pdfButton.style.cssText = `
      background: #2196F3;
      color: white;
      border: none;
      padding: 10px 20px;
      border-radius: 5px;
      cursor: pointer;
      font-size: 14px;
      transition: background-color 0.3s;
    `;
    pdfButton.onmouseover = () => pdfButton.style.background = '#1976D2';
    pdfButton.onmouseout = () => pdfButton.style.background = '#2196F3';
    pdfButton.onclick = () => this.handleGeneratePDF();

    // Add Google Calendar PDF button
    const calendarPdfButton = document.createElement('button');
    calendarPdfButton.id = 'generate-from-calendar-btn';
    calendarPdfButton.className = 'pdf-generate-btn';
    calendarPdfButton.innerHTML = '📅 Generate from Google Calendar';
    calendarPdfButton.style.cssText = `
      background: #4CAF50;
      color: white;
      border: none;
      padding: 10px 20px;
      border-radius: 5px;
      cursor: pointer;
      font-size: 14px;
      transition: background-color 0.3s;
      margin-left: 5px;
    `;
    calendarPdfButton.onmouseover = () => calendarPdfButton.style.background = '#45a049';
    calendarPdfButton.onmouseout = () => calendarPdfButton.style.background = '#4CAF50';
    calendarPdfButton.onclick = () => this.generateFromCalendar(this.currentWeekStart.toISOString());

    // Add label
    const label = document.createElement('label');
    label.textContent = 'Week starting:';
    label.style.cssText = 'font-weight: bold; color: #333;';

    // Assemble controls
    controlContainer.appendChild(label);
    controlContainer.appendChild(weekSelector);
    controlContainer.appendChild(pdfButton);
    controlContainer.appendChild(calendarPdfButton);

    // Insert into page - try multiple locations
    const insertLocations = [
      '.calendar-controls',
      '.pdf-controls',
      '#pdfControls',
      '.controls',
      'header',
      'body'
    ];

    let inserted = false;
    for (const selector of insertLocations) {
      const target = document.querySelector(selector);
      if (target) {
        target.appendChild(controlContainer);
        inserted = true;
        break;
      }
    }

    if (!inserted) {
      document.body.insertBefore(controlContainer, document.body.firstChild);
    }
  }

  // Handle PDF generation
  async handleGeneratePDF() {
    if (!this.pdfGenerator) {
      console.error('PDF generator not initialized');
      return;
    }
    
    const weekStartDate = this.currentWeekStart.toISOString().split('T')[0];
    
    // Generate PDF with reMarkable optimizations
    const success = await this.pdfGenerator.generatePDF(weekStartDate, {
      optimizeForRemarkable: true,
      includeWeeklyOverview: true,
      includeDailyPages: true
    });
    
    if (success) {
      this.showSuccessMessage('reMarkable PDF generated successfully! Check your downloads.');
    }
  }

  showSuccessMessage(message) {
    const notification = document.createElement('div');
    notification.className = 'success-notification';
    notification.textContent = message;
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: #4CAF50;
      color: white;
      padding: 15px;
      border-radius: 5px;
      z-index: 1000;
    `;
    document.body.appendChild(notification);
    
    setTimeout(() => {
      document.body.removeChild(notification);
    }, 3000);
  }
}

// CSS for the spinner animation
const spinnerStyles = `
  .spinner {
    display: inline-block;
    width: 12px;
    height: 12px;
    border: 2px solid #ffffff;
    border-radius: 50%;
    border-top-color: transparent;
    animation: spin 1s ease-in-out infinite;
  }
  
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
`;

// Inject spinner CSS if not already present
if (!document.getElementById('remarkable-pdf-styles')) {
  const styleSheet = document.createElement('style');
  styleSheet.id = 'remarkable-pdf-styles';
  styleSheet.textContent = spinnerStyles;
  document.head.appendChild(styleSheet);
}

// Initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeRemarkablePDF);
} else {
  initializeRemarkablePDF();
}

function initializeRemarkablePDF() {
  // Create global instance
  window.remarkablePDFIntegration = new CalendarPDFIntegration();
  
  // Initialize immediately with empty array - will be updated when events are synced
  window.remarkablePDFIntegration.initialize([]);
  
  // Also set up observer for when calendar data becomes available
  const checkInterval = setInterval(() => {
    // Try to access calendarEvents from the global scope
    const calendarEventsElement = document.querySelector('script');
    if (window.calendarEvents) {
      clearInterval(checkInterval);
      window.remarkablePDFIntegration.pdfGenerator = new RemarkablePDFGenerator(window.calendarEvents);
      console.log('reMarkable PDF generator updated with calendar events!');
    }
  }, 1000);
  
  // Add a global function that can be called when events are synced
  window.updateRemarkablePDFEvents = function(events) {
    if (window.remarkablePDFIntegration && events) {
      window.remarkablePDFIntegration.pdfGenerator = new RemarkablePDFGenerator(events);
      console.log(`reMarkable PDF generator updated with ${events.length} events`);
    }
  };
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { RemarkablePDFGenerator, CalendarPDFIntegration };
}