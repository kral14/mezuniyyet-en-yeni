document.addEventListener('DOMContentLoaded', async () => {
    const monthYearStr = document.getElementById('month-year-str');
    const prevMonthBtn = document.getElementById('prev-month-btn');
    const nextMonthBtn = document.getElementById('next-month-btn');
    const calendarDays = document.getElementById('calendar-days');
    const colorLegend = document.getElementById('legend-items');
    const modal = document.getElementById('vacation-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalBody = document.getElementById('modal-body');
    const closeModal = document.querySelector('.close');

    let currentDate = new Date();
    let vacationData = {}; // Boş obyekt
    
    // DÜZƏLİŞ: Status əsaslı rəng palitası  
    const statusColors = {
        "red": "#FF6B6B",           // Bitmiş məzuniyyətlər
        "green": "#4ECDC4",         // Davam edən məzuniyyətlər  
        "#007bff": "#45B7D1",       // Planlaşdırılan məzuniyyətlər
        "#E49B0F": "#FFEAA7",       // Gözləyən məzuniyyətlər
        "gray": "#85929E",          // Rədd edilmiş məzuniyyətlər
        "black": "#2C3E50"          // Xəta vəziyyəti
    };

    // --- YENİ HİSSƏ: Python-dan məlumatları alırıq ---
    try {
        // pywebview hazır olana qədər gözləyirik
        if (window.pywebview && window.pywebview.api) {
            await window.pywebview.api.isReady; 
            console.log("Python API hazır. Məlumatlar sorğulanır...");
            vacationData = await window.pywebview.api.get_vacations();
            console.log("Məlumatlar alındı:", vacationData);
            
            // Rəng əfsanəsini yaradırıq
            createStatusLegend();
        }
    } catch (e) {
        console.error("Python API ilə əlaqə qurula bilmədi:", e);
        
        // Demo məlumatları (Python API işləməzsə)
        vacationData = {
            vacations: [
                {
                    employee: "Nigar Əliyeva",
                    start_date: "2024-12-25",
                    end_date: "2024-12-30",
                    status: "approved"
                },
                {
                    employee: "Rəşad Məmmədov", 
                    start_date: "2024-12-28",
                    end_date: "2025-01-05",
                    status: "approved"
                }
            ]
        };
        
        createStatusLegend();
    }
    // --- YENİ HİSSƏNİN SONU ---

    function createStatusLegend() {
        colorLegend.innerHTML = '';
        
        const statusInfo = [
            {"status": "Bitmiş", "color": statusColors["red"], "description": "Artıq başa çatan məzuniyyətlər"},
            {"status": "Davam edən", "color": statusColors["green"], "description": "Hazırda davam edən məzuniyyətlər"},  
            {"status": "Planlaşdırılan", "color": statusColors["#007bff"], "description": "Gələcəkdə planlaşdırılan məzuniyyətlər"},
            {"status": "Gözləyir", "color": statusColors["#E49B0F"], "description": "Təsdiq gözləyən sorğular"},
            {"status": "Rədd edilib", "color": statusColors["gray"], "description": "Rədd edilmiş sorğular"}
        ];
        
        statusInfo.forEach(item => {
            const legendItem = document.createElement('div');
            legendItem.className = 'legend-item';
            legendItem.innerHTML = `
                <div class="legend-color" style="background-color: ${item.color}"></div>
                <div class="legend-name">${item.status}</div>
            `;
            legendItem.title = item.description;
            colorLegend.appendChild(legendItem);
        });
    }

    function getVacationStatusAndColor(vacation) {
        const today = new Date();
        const startDate = new Date(vacation.start_date);
        const endDate = new Date(vacation.end_date);
        const status = vacation.status || 'approved';
        
        if (status === 'pending') {
            return { color: statusColors["#E49B0F"], text: "[Gözləyir]" };
        }
        if (status === 'rejected') {
            return { color: statusColors["gray"], text: "[Rədd edilib]" };
        }
        if (status === 'approved') {
            if (endDate < today) {
                return { color: statusColors["red"], text: "[Bitmiş]" };
            } else if (startDate <= today && today <= endDate) {
                return { color: statusColors["green"], text: "[Davam edən]" };
            } else {
                return { color: statusColors["#007bff"], text: "[Planlaşdırılan]" };
            }
        }
        
        return { color: statusColors["black"], text: "[Naməlum]" };
    }

    function renderCalendar() {
        const year = currentDate.getFullYear();
        const month = currentDate.getMonth();

        const monthNames = [
            "Yanvar", "Fevral", "Mart", "Aprel", "May", "İyun",
            "İyul", "Avqust", "Sentyabr", "Oktyabr", "Noyabr", "Dekabr"
        ];
        
        monthYearStr.textContent = `${monthNames[month]} ${year}`;
        calendarDays.innerHTML = '';

        const firstDayOfMonth = new Date(year, month, 1).getDay();
        const daysInMonth = new Date(year, month + 1, 0).getDate();
        const startDay = (firstDayOfMonth === 0) ? 6 : firstDayOfMonth - 1;

        // Boş günlər
        for (let i = 0; i < startDay; i++) {
            const emptyDay = document.createElement('div');
            emptyDay.classList.add('day', 'empty');
            calendarDays.appendChild(emptyDay);
        }

        // Həqiqi günlər
        for (let i = 1; i <= daysInMonth; i++) {
            const dayElement = document.createElement('div');
            dayElement.classList.add('day');
            dayElement.textContent = i;
            
            const currentDayStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(i).padStart(2, '0')}`;
            const dayOfWeek = new Date(year, month, i).getDay();
            
            // Həftə sonu
            if (dayOfWeek === 0 || dayOfWeek === 6) {
                dayElement.classList.add('weekend');
            }
            
            // Bu gün
            const today = new Date();
            if (i === today.getDate() && month === today.getMonth() && year === today.getFullYear()) {
                dayElement.classList.add('today');
            }

            // Məzuniyyətləri yoxlayırıq
            const vacationsOnThisDay = vacationData.vacations?.filter(v => 
                v.start_date <= currentDayStr && v.end_date >= currentDayStr
            ) || [];

            if (vacationsOnThisDay.length > 0) {
                dayElement.classList.add('has-vacation');
                
                if (vacationsOnThisDay.length === 1) {
                    const vacation = vacationsOnThisDay[0];
                    
                    // DÜZƏLİŞ: Status əsaslı rəng seçimi
                    const statusInfo = getVacationStatusAndColor(vacation);
                    const color = statusInfo.color;
                    
                    dayElement.style.backgroundColor = color;
                    dayElement.dataset.employee = vacation.employee;
                    
                    // Mətn rəngini tənzimləyirik
                    if (isDarkColor(color)) {
                        dayElement.style.color = 'white';
                    }
                    
                    // Başlama və bitmə günlərini işarələyirik
                    if (vacation.start_date === currentDayStr) {
                        dayElement.classList.add('vacation-start');
                    }
                    if (vacation.end_date === currentDayStr) {
                        dayElement.classList.add('vacation-end');
                    }
                    
                } else {
                    // Çoxlu məzuniyyət - qarışıq rəng göstəririk
                    dayElement.classList.add('multiple-vacations');
                    dayElement.style.color = 'white';
                    
                    // İlk məzuniyyətin rəngini əsas götürürük
                    const firstVacation = vacationsOnThisDay[0];
                    const statusInfo = getVacationStatusAndColor(firstVacation);
                    dayElement.style.backgroundColor = statusInfo.color;
                }
                
                // Tooltip yaradırıq
                createTooltip(dayElement, vacationsOnThisDay);
                
                // Klik hadisəsi
                dayElement.addEventListener('click', () => {
                    showVacationModal(vacationsOnThisDay, i, monthNames[month], year);
                });
            }

            calendarDays.appendChild(dayElement);
        }
    }

    function isDarkColor(hexColor) {
        const hex = hexColor.replace('#', '');
        const r = parseInt(hex.substr(0, 2), 16);
        const g = parseInt(hex.substr(2, 2), 16);
        const b = parseInt(hex.substr(4, 2), 16);
        const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
        return luminance < 0.5;
    }

    function createTooltip(element, vacations) {
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip';
        
        let tooltipContent = '';
        vacations.forEach(vacation => {
            const startDate = new Date(vacation.start_date).toLocaleDateString('az-AZ');
            const endDate = new Date(vacation.end_date).toLocaleDateString('az-AZ');
            const statusInfo = getVacationStatusAndColor(vacation);
            tooltipContent += `${vacation.employee}: ${startDate} - ${endDate}<br>Status: ${statusInfo.text}<br><br>`;
        });
        
        tooltip.innerHTML = tooltipContent;
        document.body.appendChild(tooltip);
        
        element.addEventListener('mouseenter', (e) => {
            const rect = element.getBoundingClientRect();
            tooltip.style.left = rect.left + 'px';
            tooltip.style.top = (rect.top - tooltip.offsetHeight - 10) + 'px';
            tooltip.classList.add('show');
        });
        
        element.addEventListener('mouseleave', () => {
            tooltip.classList.remove('show');
        });
    }

    function showVacationModal(vacations, day, month, year) {
        modalTitle.textContent = `${day} ${month} ${year} - Məzuniyyət Məlumatları`;
        
        let modalContent = '';
        vacations.forEach(vacation => {
            const startDate = new Date(vacation.start_date).toLocaleDateString('az-AZ');
            const endDate = new Date(vacation.end_date).toLocaleDateString('az-AZ');
            const statusInfo = getVacationStatusAndColor(vacation);
            const color = statusInfo.color;
            
            modalContent += `
                <div style="margin-bottom: 15px; padding: 15px; border-left: 4px solid ${color}; background-color: ${color}20; border-radius: 5px;">
                    <h4 style="margin: 0 0 10px 0; color: ${color};">${vacation.employee}</h4>
                    <p style="margin: 5px 0;"><strong>Başlama:</strong> ${startDate}</p>
                    <p style="margin: 5px 0;"><strong>Bitmə:</strong> ${endDate}</p>
                    <p style="margin: 5px 0;"><strong>Status:</strong> ${statusInfo.text}</p>
                    ${vacation.note ? `<p style="margin: 5px 0;"><strong>Qeyd:</strong> ${vacation.note}</p>` : ''}
                </div>
            `;
        });
        
        modalBody.innerHTML = modalContent;
        modal.style.display = 'block';
        
        // Python tərəfinə məlumat göndəririk (varsa)
        if (window.pywebview && window.pywebview.api && vacations.length === 1) {
            try {
                window.pywebview.api.on_day_click(vacations[0].employee);
            } catch (e) {
                console.log("Python API çağırışı uğursuz:", e);
            }
        }
    }

    function closeModalFunction() {
        modal.style.display = 'none';
    }

    // Event listeners
    prevMonthBtn.addEventListener('click', () => {
        currentDate.setMonth(currentDate.getMonth() - 1);
        renderCalendar();
    });

    nextMonthBtn.addEventListener('click', () => {
        currentDate.setMonth(currentDate.getMonth() + 1);
        renderCalendar();
    });

    closeModal.addEventListener('click', closeModalFunction);
    
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModalFunction();
        }
    });

    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeModalFunction();
        } else if (e.key === 'ArrowLeft') {
            currentDate.setMonth(currentDate.getMonth() - 1);
            renderCalendar();
        } else if (e.key === 'ArrowRight') {
            currentDate.setMonth(currentDate.getMonth() + 1);
            renderCalendar();
        }
    });

    // Touch support for mobile
    let touchStartX = 0;
    calendarDays.addEventListener('touchstart', (e) => {
        touchStartX = e.touches[0].clientX;
    });

    calendarDays.addEventListener('touchend', (e) => {
        const touchEndX = e.changedTouches[0].clientX;
        const diff = touchStartX - touchEndX;
        
        if (Math.abs(diff) > 50) { // Minimum swipe distance
            if (diff > 0) {
                // Swipe left - next month
                currentDate.setMonth(currentDate.getMonth() + 1);
            } else {
                // Swipe right - previous month
                currentDate.setMonth(currentDate.getMonth() - 1);
            }
            renderCalendar();
        }
    });

    // İlk təqvimi çəkirik
    renderCalendar();
}); 