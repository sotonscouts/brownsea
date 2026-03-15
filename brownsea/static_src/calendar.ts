import { Calendar } from '@fullcalendar/core';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import listPlugin from '@fullcalendar/list';

class CalendarWidget extends HTMLElement {
    private calendar: Calendar | null = null;

    connectedCallback() {
        const eventsUrl = this.getAttribute('events-url');
        
        if (!eventsUrl) {
            console.error('No events-url attribute provided for calendar-widget');
            return;
        }

        this.render(eventsUrl);
    }

    disconnectedCallback() {
        if (this.calendar) {
            this.calendar.destroy();
        }
    }

    private render(eventsUrl: string): void {
        // Create calendar container
        const calendarEl = document.createElement('div');
        calendarEl.id = 'fullcalendar';
        this.appendChild(calendarEl);

        this.calendar = new Calendar(calendarEl, {
            plugins: [dayGridPlugin, timeGridPlugin, listPlugin],
            initialView: 'dayGridMonth',
            locale: 'en-GB',
            firstDay: 1, // Monday
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek,listMonth'
            },
            events: eventsUrl,
            eventDisplay: 'block',
            displayEventTime: true,
            displayEventEnd: true,
            height: 'auto',
            eventTimeFormat: {
                hour: '2-digit',
                minute: '2-digit',
                hour12: false
            },
            loading: (isLoading) => {
                if (isLoading) {
                    calendarEl.style.opacity = '0.5';
                } else {
                    calendarEl.style.opacity = '1';
                }
            }
        });

        this.calendar.render();
        
        console.log('Calendar initialized with events URL:', eventsUrl);
    }
}

// Register the custom element only if not already registered
if (!customElements.get('calendar-widget')) {
    customElements.define('calendar-widget', CalendarWidget);
}

export default CalendarWidget;
