document.addEventListener("DOMContentLoaded", function () {

    const program =
        document.getElementById("attendance_program_id");

    const semester =
        document.getElementById("attendance_semester_id");

    const subject =
        document.getElementById("attendance_subject_id");

    const studentsContainer =
        document.getElementById("students_container");


    // Program → Semester

    program.addEventListener("change", function () {

        const programId = this.value;

        semester.innerHTML =
            '<option value="">Loading...</option>';

        subject.innerHTML =
            '<option value="">Select Semester First</option>';

        studentsContainer.innerHTML =
            '<p>Select Subject to load students.</p>';


        if (programId === "") {

            semester.innerHTML =
                '<option value="">Select Program First</option>';

            return;
        }


        fetch("/get_attendance_semesters/" + programId)

            .then(response => response.json())

            .then(data => {

                semester.innerHTML =
                    '<option value="">Select Semester</option>';

                data.forEach(item => {

                    const option =
                        document.createElement("option");

                    option.value =
                        item.Semester_ID;

                    option.textContent =
                        item.Semester_Name;

                    semester.appendChild(option);

                });

            });

    });


    // Semester → Subject

    semester.addEventListener("change", function () {

        const programId =
            program.value;

        const semesterId =
            this.value;


        subject.innerHTML =
            '<option value="">Loading...</option>';


        if (semesterId === "") {

            subject.innerHTML =
                '<option value="">Select Semester First</option>';

            return;
        }


        fetch(
            "/get_attendance_subjects/"
            + programId
            + "/"
            + semesterId
        )

            .then(response => response.json())

            .then(data => {

                subject.innerHTML =
                    '<option value="">Select Subject</option>';

                data.forEach(item => {

                    const option =
                        document.createElement("option");

                    option.value =
                        item.Subject_ID;

                    option.textContent =
                        item.Subject_Name;

                    subject.appendChild(option);

                });

            });

    });


    // Subject → Students

    subject.addEventListener("change", function () {

        const programId =
            program.value;

        const semesterId =
            semester.value;

        const subjectId =
            this.value;


        if (subjectId === "") {

            studentsContainer.innerHTML =
                '<p>Select Subject to load students.</p>';

            return;
        }


        studentsContainer.innerHTML =
            '<p>Loading students...</p>';


        fetch(
            "/get_attendance_students/"
            + programId
            + "/"
            + semesterId
            + "/"
            + subjectId
        )

            .then(response => response.json())

            .then(data => {

                if (data.length === 0) {

                    studentsContainer.innerHTML =
                        '<p>No students found.</p>';

                    return;
                }


                let html = `
                    <h3>Students</h3>

                    <table border="1">

                        <tr>
                            <th>Roll No</th>
                            <th>Name</th>
                            <th>Attendance</th>
                        </tr>
                `;


                data.forEach(student => {

                    html += `

                        <tr>

                            <td>
                                ${student.Roll_No}
                            </td>

                            <td>
                                ${student.Name}
                            </td>

                            <td>

                                <label>
                                    <input
                                        type="radio"
                                        name="status_${student.Student_ID}"
                                        value="Present"
                                        checked
                                    >
                                    Present
                                </label>

                                <label>
                                    <input
                                        type="radio"
                                        name="status_${student.Student_ID}"
                                        value="Absent"
                                    >
                                    Absent
                                </label>

                            </td>

                        </tr>

                    `;

                });


                html += "</table>";

                studentsContainer.innerHTML = html;

            });

    });

});