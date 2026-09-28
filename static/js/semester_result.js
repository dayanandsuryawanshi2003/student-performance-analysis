const programSelect =
    document.getElementById("result_program");

const semesterSelect =
    document.getElementById("result_semester");

const subjectSelect =
    document.getElementById("result_subject");

const subjectTypeSection =
    document.getElementById("subject_type_section");

const studentSection =
    document.getElementById("result_student_section");


// =====================================
// PROGRAM → SEMESTER + SUBJECT
// =====================================

programSelect.addEventListener("change", function () {

    const programId = this.value;

    semesterSelect.innerHTML =
        '<option value="">Loading Semesters...</option>';

    subjectSelect.innerHTML =
        '<option value="">Loading Subjects...</option>';

    subjectTypeSection.innerHTML = "";

    studentSection.innerHTML =
        '<p>Select Subject and Semester.</p>';


    if (!programId) {

        semesterSelect.innerHTML =
            '<option value="">Select Program First</option>';

        subjectSelect.innerHTML =
            '<option value="">Select Program First</option>';

        return;
    }


    // =================================
    // LOAD SEMESTERS
    // =================================

    fetch(`/get_result_semesters/${programId}`)

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


    // =================================
    // LOAD SUBJECTS
    // =================================

    fetch(`/get_subjects_by_program/${programId}`)

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

                option.dataset.type =
                    subject.Subject_Type;

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


// =====================================
// SUBJECT CHANGE
// =====================================

subjectSelect.addEventListener("change", function () {

    const subjectId =
        this.value;

    const selectedOption =
        this.options[this.selectedIndex];

    const subjectType =
        selectedOption.dataset.type;


    subjectTypeSection.innerHTML = "";

    studentSection.innerHTML =
        '<p>Select Semester to load students.</p>';


    if (!subjectId) {

        return;
    }


    // Show automatically detected type

    subjectTypeSection.innerHTML = `

        <strong>Subject Type:</strong>
        ${subjectType}

    `;


    loadStudentsIfReady();

});


// =====================================
// SEMESTER CHANGE
// =====================================

semesterSelect.addEventListener("change", function () {

    loadStudentsIfReady();

});


// =====================================
// LOAD STUDENTS
// =====================================

function loadStudentsIfReady() {

    const subjectId =
        subjectSelect.value;

    const semesterId =
        semesterSelect.value;


    if (!subjectId || !semesterId) {

        return;
    }


    studentSection.innerHTML =
        '<p>Loading students...</p>';


    fetch(
        `/get_result_students/${subjectId}/${semesterId}`
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

                        <th>Marks</th>

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
                                name="marks[]"
                                min="0"
                                step="1"
                                required
                            >

                        </td>

                    </tr>

                `;

            });


            table += `</table>`;

            studentSection.innerHTML =
                table;

        })

        .catch(error => {

            console.error(error);

            studentSection.innerHTML =
                '<p>Error loading students.</p>';

        });

}