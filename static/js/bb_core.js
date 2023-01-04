function load_students_for_classgroup_page(classgroup_id) {

    let all_students_list = document.getElementById("student_list"); // sl = student_list; list of all students
    let medical_students_list = document.getElementById("key_students_medical");
    let sen_students_list = document.getElementById("key_students_sen");
    let tilt_students_list = document.getElementById("key_students_tilt");
    let behaviour_events = [];

    let xhr = new XMLHttpRequest();

    xhr.onreadystatechange = function () {

        if (xhr.status == 200 && xhr.readyState == 4) {
            all_students_list.innerHTML = "";

            let response_data = JSON.parse(xhr.responseText);

            let collection_type = response_data['type'];
            let students_data = response_data['students'];

            let sen_count = 0, tilt_count = 0;

            students_data.sort(function (a, b) {
                //let keyA = new Date(a['date']), keyB = new Date(b['date']);
                if (a.last_name < b.last_name) return -1;
                if (a.last_name > b.last_name) return 1;
                return 0;
            });

            for (let i = 0; i < students_data.length; i++) {

                let s = students_data[i]; // This particular student
                let bs = s['behaviours']; // This student's behaviours

                // Add this student's behaviours to the behaviour_events list
                for (let j = 0; j < bs.length; j++) {
                    let b = bs[j]; // This particular behaviour
                    b['student_display_name'] = s['display_name']; // Add a key to this behaviour to hold the students' name
                    b['student_id'] = s['id'];
                    b['date'] = new Date(b['date']); // Convert date to a Date object
                    behaviour_events.push(b); // Add to list of all behaviour events
                }

                // As students are processed:
                // - show their name and add a div beneath with  key data, including link to BC profile
                // - check if they need adding to key students info panels, and do so
                // - add each behaviour as dict to behaviour_event list
                // - add to each behaviour dict a 'student_display_name' key and add the current student's name so that
                //  this can be shown along with the summary of the behaviour event in the timeline
                all_students_list.innerHTML += `<li><a href="https://cloudmis.bromcom.com/Nucleus/UI/Areas/Students/StudentDetails.aspx?StudentIDs=${s['id']}#Profile" target="_blank" style="text-decoration: none; color: black">${s['display_name']}</a>${collection_type != "Tutor Group" ? ' (' + s['tutor_group'] + ', ' + s['house'] + ')' : ''}</li>`;

                if (s['sen']) {
                    sen_students_list.innerHTML += `<li><a href="https://cloudmis.bromcom.com/Nucleus/UI/Areas/Students/StudentDetails.aspx?StudentIDs=${s['id']}#Profile" target="_blank" style="text-decoration: none; color: black">${s['display_name']}</a>${collection_type != "Tutor Group" ? ' (' + s['tutor_group'] + ', ' + s['house'] + ')' : ''}</li>`;
                    sen_count++;
                }
                if (s['tilt']) {
                    tilt_students_list.innerHTML += `<li><a href="https://cloudmis.bromcom.com/Nucleus/UI/Areas/Students/StudentDetails.aspx?StudentIDs=${s['id']}#Profile" target="_blank" style="text-decoration: none; color: black">${s['display_name']}</a>${collection_type != "Tutor Group" ? ' (' + s['tutor_group'] + ', ' + s['house'] + ')' : ''}</li>`;
                    tilt_count++;
                }

            }
            if (sen_count == 0) {
                sen_students_list.innerHTML += "<li>There are no students with SEN provision in this group.</li>"
            }
            if (tilt_count == 0) {
                tilt_students_list.innerHTML += "<li>There are no students with Tilt provision in this group.</li>"
            }
            display_behaviour_timeline(behaviour_events);
        }
    }

    xhr.open('GET', '/api/classgroup/' + classgroup_id, false);
    xhr.send();

}



function display_behaviour_timeline(behaviour_events) {

    let behaviours_list = document.getElementById("behaviours_list");
    behaviours_list.innerHTML = "";

    // Sort the behaviours list by date
    // https://stackoverflow.com/questions/8837454/sort-array-of-objects-by-single-key-with-date-value
    behaviour_events.sort(function (b, a) {
        //let keyA = new Date(a['date']), keyB = new Date(b['date']);
        if (a.date < b.date) return -1;
        if (a.date > b.date) return 1;
        return 0;
    });

    let current_date = null;

    if (behaviour_events.length > 0) {
        current_date = behaviour_events[0].date;
        console.log(current_date);
        behaviours_list.innerHTML += `<h6 class="behaviour_list_date_heading">${current_date.toDateString()}</h6>`;
    }

    for (let i = 0; i < behaviour_events.length; i++) {
        let b = behaviour_events[i];

        // Check if new date header is needed
        if (b.date.toDateString() != current_date.toDateString()) {
            current_date = new Date(b.date);
            behaviours_list.innerHTML += `<h6 class="behaviour_list_date_heading">${current_date.toDateString()}</h6>`;
        }

        behaviours_list.innerHTML += `<li>
                                            
                                            <div class="behaviour_event ${b.type == 'Positive' ? 'behaviour_event_positive' : 'behaviour_event_negative'}">
                                            <a href="https://cloudmis.bromcom.com/Nucleus/UI/Areas/Students/StudentDetails.aspx?StudentIDs=${b['student_id']}#Behaviour" target="_blank" style="text-decoration: none"><p class="behaviour_event_student_name">${b['student_display_name']}</p></a>
                                            <p class="behaviour_event_description">${b['description']}: ${b['comment'] != "" ? b['comment'] : '<span class=\"behaviour_event_no_comment_text\">No comment provided.</span>'}</p>
                                            <p class="behaviour_event_meta_data">${b.date.toLocaleTimeString().substring(0, 5)} <span class="behaviour_event_subject">${b['subject'] != null ? b['subject'] : 'No subject'}</span> <span class="behaviour_event_staff_code">(${b['staff_code']})</span></p>
                                            </div>
                                    </li>`;
    }
}

function search_classgroup() {
    let search_button = document.getElementById("classgroup_search_button");
    let search_field = document.getElementById("classgroup_search_input");

    // Prevent other searches taking place whilst the page is loading
    search_button.disabled = true;
    search_field.disabled = true;

    let new_page_url = "/class?name=" + search_field.value;
    // alert(new_page_url);
    window.location.assign(new_page_url);

}

function page_load(classgroup_id) {
    load_students_for_classgroup_page(classgroup_id);
    document.getElementById("classgroup_search_input").addEventListener('keydown', (e) => {

        if (!e.repeat && e.key == "Enter") {
            search_classgroup();

        }
    });
}




