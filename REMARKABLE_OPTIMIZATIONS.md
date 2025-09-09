# reMarkable Paper Pro Move Calendar Optimizations

## Overview
This calendar application has been specifically optimized for the **reMarkable Paper Pro Move** device with its 7.3" e-ink display (227 DPI). The application provides a professional calendar system with Google Calendar integration, optimized for the unique display characteristics and usage patterns of the reMarkable device.

## Device Specifications Addressed

### reMarkable Paper Pro Move
- **Display Size**: 7.3 inches
- **Resolution**: 227 DPI
- **Dimensions**: 
  - Landscape: 163mm × 91mm
  - Portrait: 91mm × 163mm
- **Display Type**: E-ink (optimized for high contrast, minimal refresh)

## Key Optimizations Implemented

### 1. Orientation-Specific Layouts

#### Weekly View (Landscape - 163mm × 91mm)
- **Purpose**: Overview of entire week's schedule
- **Layout**: Horizontal time grid with 7-day columns
- **Time Slots**: 30-minute intervals from 7:00 to 22:00
- **Sidebar**: Priority tasks, weekly goals, and notes
- **Optimized for**: Quick weekly planning and overview

#### Daily View (Portrait - 91mm × 163mm)  
- **Purpose**: Detailed daily schedule and tasks
- **Layout**: Vertical time slots with extended event details
- **Time Slots**: 30-minute intervals from 7:00 to 22:00
- **Sidebar**: Top 3 priorities, daily goals, notes
- **Optimized for**: Focused daily planning and execution

### 2. Bidirectional Navigation System

#### Event Navigation
- **Click on Weekly Event** → Navigate to specific day and time in daily view
- **Click on Daily Event** → Return to weekly view with event highlighted
- **Visual Feedback**: Events briefly highlight in yellow when navigated to

#### Navigation Controls

**Daily View Top Navigation**:
- "Return to Weekly View" button - Returns to weekly overview

**Daily View Bottom Navigation**:
- "Yesterday" button - Navigate to previous day (wraps to previous week if needed)
- "Tomorrow" button - Navigate to next day (wraps to next week if needed)

### 3. Minimalistic Design Aesthetic

#### Color Scheme
```css
--rm-black: #000000        /* Primary text */
--rm-dark-gray: #333333    /* Headers, borders */
--rm-medium-gray: #666666  /* Secondary text */
--rm-light-gray: #999999   /* Tertiary elements */
--rm-lighter-gray: #cccccc /* Grid lines */
--rm-off-white: #f5f5f5    /* Background accents */
--rm-white: #ffffff        /* Primary background */
--rm-accent: #2c3e50       /* Subtle blue-gray for events */
```

#### Typography
- **Font Family**: System fonts optimized for e-ink readability
- **Font Sizes**: Carefully scaled for 227 DPI display
  - XL: 18px (main headers)
  - LG: 14px (section headers)
  - MD: 12px (body text)
  - SM: 10px (labels)
  - XS: 8px (grid text)

### 4. PDF Export Optimizations

#### Page Settings
```javascript
// Weekly pages - Landscape
@page weekly {
  size: 163mm 91mm landscape;
  margin: 2mm;
}

// Daily pages - Portrait
@page daily {
  size: 91mm 163mm portrait;
  margin: 2mm;
}
```

#### Export Features
- First page: Weekly overview in landscape
- Pages 2-8: Daily views in portrait (Monday through Sunday)
- High contrast for e-ink display
- Minimal margins for maximum content area

### 5. E-ink Display Optimizations

#### Visual Hierarchy
- Strong contrast between elements
- Clear borders and separators
- Minimal gradients or shadows
- Optimized for grayscale display

#### Interaction Feedback
- Subtle hover states that work with e-ink refresh rates
- Clear visual indicators for clickable elements
- Smooth transitions compatible with e-ink update speeds

## Usage Instructions

### Accessing the Application

1. **Live URL**: https://3001-ivun13qxfu43uot7rdf2b-6532622b.e2b.dev
2. **Connect Google Calendar** for event synchronization
3. **Select calendars** to sync
4. **Choose sync range**: Current week or full range (2015-2030)

### Navigation Workflow

#### Starting from Weekly View
1. View entire week's schedule at a glance
2. Click any event to jump to that day's detailed view
3. Click any time slot to navigate to that specific time

#### Working in Daily View
1. See detailed schedule for the current day
2. Use "Yesterday"/"Tomorrow" buttons to navigate days
3. Click "Return to Weekly View" to go back to overview
4. Click any event to return to weekly view with that event highlighted

### PDF Generation for reMarkable

1. Click "Generate PDF" button
2. PDF will be created with:
   - Page 1: Weekly landscape view (163×91mm)
   - Pages 2-8: Daily portrait views (91×163mm)
3. Transfer PDF to reMarkable device
4. Use reMarkable's annotation features on the generated calendar

## Technical Implementation Details

### Event Management System
```javascript
class PlannerEventManager {
  - Manages bidirectional event linking
  - Tracks weekly vs daily event visibility
  - Handles event count updates
  - Maintains navigation state
}
```

### Navigation Functions
```javascript
// Navigate from weekly to daily
navigateToDay(eventDate)

// Navigate between days
navigateToPreviousDay()
navigateToNextDay()

// Return to weekly view
returnToWeeklyView()

// Highlight events after navigation
highlightEventInDailyView(event, eventDate)
highlightEventInWeeklyView(event, eventDate)
```

### Responsive Dimensions
- Weekly preview: `aspect-ratio: 163/91`
- Daily preview: `aspect-ratio: 91/163`
- Automatic dimension display updates when switching views

## Benefits for reMarkable Users

1. **Perfect Fit**: Dimensions exactly match reMarkable Paper Pro Move display
2. **Readable Text**: Font sizes optimized for 227 DPI e-ink
3. **Efficient Navigation**: Quick switching between overview and detail
4. **Annotation Ready**: PDF exports perfect for reMarkable markup
5. **Battery Friendly**: Minimal refreshes with high contrast design
6. **Professional Aesthetic**: Matches reMarkable's minimalistic design language

## Future Enhancements

- [ ] Gesture support for reMarkable stylus navigation
- [ ] Quick note fields optimized for handwriting recognition
- [ ] Template library for different planning styles
- [ ] Direct reMarkable Cloud integration
- [ ] Offline mode with local storage
- [ ] Custom event colors for better visual organization

## Support

For issues or feature requests, please check the application logs:
```bash
npx pm2 logs calendar-server --nostream
```

## License

Optimized for reMarkable Paper Pro Move by GenSpark AI Developer
© 2025 - All optimizations open source