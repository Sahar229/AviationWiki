const planes = [
    {
        name: "Airbus A350", // <--- NEW PROPERTY
        id: "0703224a1a7e497eaa2a860e1d3b1774", 
        wingspan: "60.3m", length: "73.5m", height: "17.5m", engines: "2x Rolls-Royce",
        speed: "1,098 km/h", range: "15,000 km",
        desc: "The Airbus A350 XWB is a family of long-range, wide-body airliners developed by Airbus.",
        img: "https://upload.wikimedia.org/wikipedia/commons/f/f7/EGLF_-_Airbus_A350-941_-_F-WZNW.jpg"
    },
    {
        name: "Supermarine Spitfire",
        id: "8349f26e1e88455da75dd7352b02b794", 
        wingspan: "11.2m", length: "9.1m", height: "3.9m", engines: "1x Merlin",
        speed: "595 km/h", range: "760 km",
        desc: "The Supermarine Spitfire is a British single-seat fighter aircraft used by the Royal Air Force.",
        img: "https://media.gq-magazine.co.uk/photos/61e1ccb429520b6aa015bbe4/16:9/w_2560%2Cc_limit/SP0935.03-2-2.jpg"
    },
    {
        name: "Boeing 747-8",
        id: "86ec524a08e74e5e8907771c2d96b525", 
        wingspan: "68.4m", length: "76.3m", height: "19.4m", engines: "4x GEnx",
        speed: "988 km/h", range: "14,320 km",
        desc: "The Boeing 747 is a large, long-range wide-body airliner known as the Queen of the Skies.",
        img: "https://img.mako.co.il/2019/07/10/45389754903856092413_i.jpg"
    },
    {
        name: "F-16 Fighting Falcon",
        id: "8be8ab656304467eb6ddcbb244ae8574", 
        wingspan: "9.96m", length: "15.06m", height: "4.88m", engines: "1x F110-GE-129",
        speed: "2,120 km/h", range: "4,222 km",
        desc: "A highly versatile supersonic multirole fighter aircraft originally developed for the USAF.",
        img: "https://i0.wp.com/www.flyajetfighter.com/wp-content/uploads/2022/09/f-16-fighter-jet.jpg?ssl=1"
    },
    {
        name: "Boeing 737-800",
        id: "fa2d273dba0e45348284a6d6cd711218", 
        wingspan: "35.8m", length: "39.5m", height: "12.5m", engines: "2x CFM56-7B",
        speed: "876 km/h", range: "5,460 km",
        desc: "The world's most widely used narrow-body aircraft, reliable for short-to-medium haul flights.",
        img: "https://upload.wikimedia.org/wikipedia/commons/f/ff/Delta_Boeing_737-800_N371DA_departing_Boston_June_2025.jpg"
    },
    {
        name: "Airbus A330-900neo",
        id: "6174d5427cad49a981401cd421bc8be1", 
        wingspan: "64.0m", length: "63.66m", height: "16.79m", engines: "2x Trent 7000",
        speed: "918 km/h", range: "13,334 km",
        desc: "A modern wide-body airliner known for its efficiency and quiet cabin experience.",
        img: "https://upload.wikimedia.org/wikipedia/commons/c/c0/Airbus_A330neo_F-WTTN_37.jpg"
    },
    {
        name: "Airbus A400M",
        id: "ce45851ca78143eb836fcbe287e8d241", 
        wingspan: "42.4m", length: "45.1m", height: "14.7m", engines: "4x TP400-D6 turboprops",
        speed: "781 km/h", range: "3,300 km",
        desc: "A multi-national four-engine turboprop military transport aircraft.",
        img: "https://upload.wikimedia.org/wikipedia/commons/3/31/German_Air_Force_Airbus_A400M_%28out_cropped%29.jpg"
    },
    {
        name: "Antonov An-225",
        id: "bdea66835752483e8a9ea87e5f224122", 
        wingspan: "88.4m", length: "84.0m", height: "18.1m", engines: "6x Progress D-18T",
        speed: "850 km/h", range: "15,400 km",
        desc: "The heaviest aircraft ever built and the largest wingspan of any aircraft in operational service.",
        img: "https://images.aircharterservice.com/global/aircraft-guide/cargo-charter/antonov-an-225-5.jpg"
    }
];

function changePlane(index) {
    const data = planes[index];
    
    // 1. Update Text
    document.getElementById('wingspan').innerText = data.wingspan;
    document.getElementById('length').innerText = data.length;
    document.getElementById('height').innerText = data.height;
    document.getElementById('engines').innerText = data.engines;
    document.getElementById('speed').innerText = data.speed;
    document.getElementById('range').innerText = data.range;
    document.getElementById('desc').innerText = data.desc;
    document.getElementById('info-image').src = data.img;

    // 3. Update Sketchfab Iframe
    const iframe = document.getElementById('sketchfab-frame');
    iframe.src = `https://sketchfab.com/models/${data.id}/embed?autostart=1&ui_theme=dark`;

    // 4. Update Active Button
    document.querySelectorAll('.thumbnail').forEach((t, i) => {
        if(i === index) t.classList.add('active');
        else t.classList.remove('active');
    });
}


    // --- SEARCH FUNCTIONALITY ---
const searchInput = document.getElementById('search-input');
const resultsBox = document.getElementById('search-results');

// 1. Listen for typing
searchInput.addEventListener('input', function() {
    const query = this.value.toLowerCase().trim();
    resultsBox.innerHTML = ''; // Clear previous results

    if (query.length === 0) {
        resultsBox.style.display = 'none';
        return;
    }

    // Filter planes based on name
    const matches = planes.filter(plane => plane.name.toLowerCase().includes(query));

    if (matches.length > 0) {
        matches.forEach(match => {
            const div = document.createElement('div');
            div.classList.add('search-option');
            div.innerText = match.name;
            
            // Click to switch plane
            div.onclick = () => {
                selectPlaneByName(match.name);
            };
            resultsBox.appendChild(div);
        });
    } else {
        // Display "No planes found"
        const div = document.createElement('div');
        div.classList.add('no-results');
        div.innerText = "No planes found";
        resultsBox.appendChild(div);
    }

    resultsBox.style.display = 'block';
});

// 2. Listen for "Enter" key
searchInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') {
        const query = this.value.toLowerCase().trim();
        const match = planes.find(plane => plane.name.toLowerCase().includes(query));
        
        if (match) {
            selectPlaneByName(match.name);
            this.blur(); // Remove focus from input
        }
    }
});

// 3. Helper to switch plane
function selectPlaneByName(name) {
    const index = planes.findIndex(p => p.name === name);
    if (index !== -1) {
        changePlane(index);
        searchInput.value = ''; // Clear input
        resultsBox.style.display = 'none'; // Hide box
    }
}

// 4. Close dropdown when clicking outside
document.addEventListener('click', function(e) {
    if (!searchInput.contains(e.target) && !resultsBox.contains(e.target)) {
        resultsBox.style.display = 'none';
    }
});