document.addEventListener("DOMContentLoaded", function () {

    const subjectProgram =
        document.getElementById("subject_program_id");

    const subjectSemester =
        document.getElementById("subject_semester_id");


    subjectProgram.addEventListener("change", function () {

        const programId = this.value;

        console.log("Selected Program ID:", programId);


        if (programId === "") {

            subjectSemester.innerHTML =
                '<option value="">Select Program First</option>';

            return;
        }


        subjectSemester.innerHTML =
            '<option value="">Loading...</option>';


        fetch("/get_subject_semesters/" + programId)

            .then(function (response) {

                console.log("Response status:", response.status);

                if (!response.ok) {
                    throw new Error("Failed to load semesters");
                }

                return response.json();
            })

            .then(function (data) {

                console.log("Semester data:", data);

                subjectSemester.innerHTML =
                    '<option value="">Select Semester</option>';


                data.forEach(function (semester) {

                    const option =
                        document.createElement("option");

                    option.value =
                        semester.Semester_ID;

                    option.textContent =
                        semester.Semester_Name;

                    subjectSemester.appendChild(option);

                });

            })

            .catch(function (error) {

                console.error("Error:", error);

                subjectSemester.innerHTML =
                    '<option value="">Error loading semesters</option>';

            });

    });

});