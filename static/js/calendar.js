// Calendar and Appointment Booking JavaScript
// Handles interactive calendar, time slot selection, and availability checking

document.addEventListener('DOMContentLoaded', function () {
    const calendarEl = document.getElementById('appointment-calendar');
    const timeSlotsEl = document.getElementById('time-slots');
    const selectedDateInput = document.getElementById('selected_date');
    const selectedTimeInput = document.getElementById('selected_time');

    if (!calendarEl) return;

    let currentMonth = new Date().getMonth();
    let currentYear = new Date().getFullYear();
    let selectedDate = null;
    let serviceType = 'Dental'; // Default

    // Time slots (9AM - 5PM, 30-min intervals)
    const timeSlots = [
        '09:00', '09:30', '10:00', '10:30', '11:00', '11:30',
        '12:00', '12:30', '13:00', '13:30', '14:00', '14:30',
        '15:00', '15:30', '16:00', '16:30'
    ];

    // Render calendar
    function renderCalendar() {
        const firstDay = new Date(currentYear, currentMonth, 1);
        const lastDay = new Date(currentYear, currentMonth + 1, 0);
        const prevLastDay = new Date(currentYear, currentMonth, 0);

        const firstDayIndex = firstDay.getDay();
        const lastDateNum = lastDay.getDate();
        const prevLastDateNum = prevLastDay.getDate();

        let calendar = `
            <div class="calendar-header flex items-center justify-between mb-6">
                <button type="button" onclick="previousMonth()" class="px-4 py-2 bg-deep-blue text-white rounded-lg hover:bg-opacity-90">
                    <i class="fas fa-chevron-left"></i>
                </button>
                <h3 class="text-2xl font-bold text-gray-900">
                    ${firstDay.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
                </h3>
                <button type="button" onclick="nextMonth()" class="px-4 py-2 bg-deep-blue text-white rounded-lg hover:bg-opacity-90">
                    <i class="fas fa-chevron-right"></i>
                </button>
            </div>
            <div class="grid grid-cols-7 gap-2 text-center mb-2">
                <div class="font-semibold text-gray-600 text-sm">Sun</div>
                <div class="font-semibold text-gray-600 text-sm">Mon</div>
                <div class="font-semibold text-gray-600 text-sm">Tue</div>
                <div class="font-semibold text-gray-600 text-sm">Wed</div>
                <div class="font-semibold text-gray-600 text-sm">Thu</div>
                <div class="font-semibold text-gray-600 text-sm">Fri</div>
                <div class="font-semibold text-gray-600 text-sm">Sat</div>
            </div>
            <div class="grid grid-cols-7 gap-2">
        `;

        // Previous month's trailing dates
        for (let i = firstDayIndex; i > 0; i--) {
            calendar += `<div class="p-3 text-gray-300 text-center">${prevLastDateNum - i + 1}</div>`;
        }

        // Current month dates
        const today = new Date();
        for (let day = 1; day <= lastDateNum; day++) {
            const date = new Date(currentYear, currentMonth, day);
            const dateStr = date.toISOString().split('T')[0];
            const isPast = date < today.setHours(0, 0, 0, 0);

            let classes = 'p-3 rounded-lg text-center cursor-pointer transition-all hover:scale-105';

            if (isPast) {
                classes += ' calendar-date-past';
            } else {
                classes += ' bg-gray-100 hover:bg-gray-200 text-gray-900';
            }

            calendar += `<div class="${classes}" onclick="selectDate('${dateStr}')" data-date="${dateStr}">${day}</div>`;
        }

        calendar += '</div>';
        calendarEl.innerHTML = calendar;

        // Fetch availability for visible dates
        fetchAvailabilityForMonth();
    }

    // Fetch availability
    async function fetchAvailabilityForMonth() {
        // This would call the backend API to get availability
        // For now, we'll simulate it
        setTimeout(() => {
            document.querySelectorAll('[data-date]').forEach(el => {
                const dateStr = el.getAttribute('data-date');
                const randomSlots = Math.floor(Math.random() * 20);

                if (!el.classList.contains('calendar-date-past')) {
                    el.classList.remove('bg-gray-100');
                    if (randomSlots >= 16) {
                        el.classList.add('calendar-date-full');
                        el.onclick = null;
                    } else if (randomSlots > 8) {
                        el.classList.add('calendar-date-partial');
                    } else {
                        el.classList.add('calendar-date-available');
                    }
                }
            });
        }, 300);
    }

    // Select date
    window.selectDate = function (dateStr) {
        selectedDate = dateStr;
        selectedDateInput.value = dateStr;

        // Highlight selected
        document.querySelectorAll('[data-date]').forEach(el => {
            el.classList.remove('ring-4', 'ring-deep-blue');
        });
        document.querySelector(`[data-date="${dateStr}"]`).classList.add('ring-4', 'ring-deep-blue');

        // Load time slots
        loadTimeSlots(dateStr);
    };

    // Load time slots
    function loadTimeSlots(dateStr) {
        timeSlotsEl.innerHTML = '<p class="text-gray-500 text-center py-4">Loading available time slots...</p>';

        // Simulate API call
        setTimeout(() => {
            let html = '<div class="grid grid-cols-4 gap-3">';

            timeSlots.forEach(slot => {
                const isAvailable = Math.random() > 0.3; // Simulate availability

                if (isAvailable) {
                    html += `
                        <button type="button" onclick="selectTimeSlot('${slot}')" 
                            class="time-slot-btn p-3 border-2 border-gray-300 rounded-lg hover:border-deep-blue hover:bg-blue-50 transition-all text-sm font-semibold"
                            data-time="${slot}">
                            ${formatTime(slot)}
                        </button>
                    `;
                } else {
                    html += `
                        <button type="button" disabled
                            class="p-3 border-2 border-gray-200 rounded-lg bg-gray-100 text-gray-400 cursor-not-allowed text-sm">
                            ${formatTime(slot)}
                        </button>
                    `;
                }
            });

            html += '</div>';
            timeSlotsEl.innerHTML = html;
        }, 300);
    }

    // Select time slot
    window.selectTimeSlot = function (time) {
        selectedTimeInput.value = time;

        // Highlight selected
        document.querySelectorAll('.time-slot-btn').forEach(btn => {
            btn.classList.remove('border-deep-blue', 'bg-blue-50', 'text-deep-blue');
            btn.classList.add('border-gray-300');
        });

        const btn = document.querySelector(`[data-time="${time}"]`);
        btn.classList.add('border-deep-blue', 'bg-blue-50', 'text-deep-blue');
        btn.classList.remove('border-gray-300');
    };

    // Format time
    function formatTime(time) {
        const [hours, mins] = time.split(':');
        const h = parseInt(hours);
        const ampm = h >= 12 ? 'PM' : 'AM';
        const displayHour = h > 12 ? h - 12 : h === 0 ? 12 : h;
        return `${displayHour}:${mins} ${ampm}`;
    }

    // Navigation
    window.previousMonth = function () {
        currentMonth--;
        if (currentMonth < 0) {
            currentMonth = 11;
            currentYear--;
        }
        renderCalendar();
    };

    window.nextMonth = function () {
        currentMonth++;
        if (currentMonth > 11) {
            currentMonth = 0;
            currentYear++;
        }
        renderCalendar();
    };

    // Initialize
    renderCalendar();
});
