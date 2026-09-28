const programSelect = document.getElementById("assignment_program");
const semesterSelect = document.getElementById("assignment_semester");
const subjectSelect = document.getElementById("assignment_subject");
const studentSection = document.getElementById("student_section");


/* ================================
   PROGRAM → SEMESTER
================================ */

programSelect.addEventListener("change", function () {

    const programId = this.value;

    semesterSelect.innerHTML =
        '<option value="">Loading Semesters...</option>';

    subjectSelect.innerHTML =
        '<option value="">Select Semester First</option>';

    studentSection.innerHTML =
        '<p>Select a subject to load students.</p>';


    if (!programId) {

        semesterSelect.innerHTML =
            '<option value="">Select Program First</option>';

        return;
    }


    fetch(`/get_assignment_semesters/${programId}`)

        .then(response => {

            if (!response.ok) {
                throw new Error("Failed to load semesters");
            }

            return response.json();

        })

        .then(data => {

            semesterSelect.innerHTML =
                '<option value="">Select Semester</option>';


            data.forEach(semester => {

                const option =
                    document.createElement("option");

                option.value =
                    semester.Semester_ID;

                option.textContent =
                    semester.Semester_Name;

                semesterSelect.appendChild(option);

            });

        })

        .catch(error => {

            console.error(error);

            semesterSelect.innerHTML =
                '<option value="">Error loading semesters</option>';

        });

});


/* ================================
   SEMESTER → SUBJECT
================================ */

semesterSelect.addEventListener("change", function () {

    const programId =
        programSelect.value;

    const semesterId =
        this.value;


    subjectSelect.innerHTML =
        '<option value="">Loading Subjects...</option>';

    studentSection.innerHTML =
        '<p>Select a subject to load students.</p>';


    if (!semesterId) {

        subjectSelect.innerHTML =
            '<option value="">Select Semester First</option>';

        return;
    }


    fetch(
        `/get_assignment_subjects/${programId}/${semesterId}`
    )

        .then(response => {

            if (!response.ok) {
                throw new Error("Failed to load subjects");
            }

            return response.json();

        })

        .then(data => {

            subjectSelect.innerHTML =
                '<option value="">Select Subject</option>';


            data.forEach(subject => {

                const option =
                    document.createElement("option");

                option.value =
                    subject.Subject_ID;

                option.textContent =
                    `${subject.Subject_Name} (${subject.Subject_Type})`;

                subjectSelect.appendChild(option);

            });

        })

        .catch(error => {

            console.error(error);

            subjectSelect.innerHTML =
                '<option value="">Error loading subjects</option>';

        });

});


/* ================================
   SUBJECT → STUDENTS
================================ */

subjectSelect.addEventListener("change", function () {

    const subjectId =
        this.value;

    const semesterId =
        semesterSelect.value;


    if (!subjectId) {

        studentSection.innerHTML =
            '<p>Select a subject.</p>';

        return;
    }


    studentSection.innerHTML =
        '<p>Loading students...</p>';


    fetch(
        `/get_assignment_students/${subjectId}/${semesterId}`
    )

        .then(response => {

            if (!response.ok) {
                throw new Error("Failed to load students");
            }

            return response.json();

        })

        .then(data => {

            if (data.length === 0) {

                studentSection.innerHTML =
                    '<p>No students assigned to this subject.</p>';

                return;
            }


            let table = `

                <h3>Students</h3>

                <table border="1">

                    <tr>
                        <th>Roll No</th>
                        <th>Student Name</th>
                        <th>Assignment 1</th>
                        <th>Assignment 2</th>
                    </tr>

            `;


            data.forEach(student => {

                table += `

                    <tr>

                        <td>
                            ${student.Roll_No}
                        </td>

                        <td>
                            ${student.Name}
                        </td>

                        <td>

                            <input
                                type="hidden"
                                name="student_id[]"
                                value="${student.Student_ID}"
                            >

                            <input
                                type="number"
                                name="assignment_1[]"
                                min="0"
                                max="100"
                                step="1"
                            >

                        </td>

                        <td>

                            <input
                                type="number"
                                name="assignment_2[]"
                                min="0"
                                max="100"
                                step="1"
                            >

                        </td>

                    </tr>

                `;

            });


            table += `</table>`;

            studentSection.innerHTML = table;

        })

        .catch(error => {

            console.error(error);

            studentSection.innerHTML =
                '<p>Error loading students.</p>';

        });

});