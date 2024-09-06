let currentDot = 2;
let totalDot = 0;
let data = {};

function startProcess() {
    totalDot = parseInt(document.getElementById('numOfDot').value);
    const errorContainer = document.getElementById('errorContainer');

    if (totalDot > 0 && totalDot <= 6) {
        errorContainer.innerHTML = '';
        document.getElementById('startButton').disabled = true;
        addInputFields(currentDot);
    } else {
        errorContainer.innerHTML = 'Vui lòng nhập số đợt từ 1 đến 6!';
    }
}

function addInputFields(dot) {
    const container = document.getElementById('inputContainer');
    container.innerHTML = '';

    const formGroup = document.createElement('div');
    formGroup.className = 'form-group';

    formGroup.innerHTML = `
        <label>Đợt ${dot}</label>
        <div id="subjects_${dot}">
            <input type="text" id="maMon_${dot}_1" placeholder="Nhập mã môn học (tối đa 6 số)" maxlength="6" pattern="\\d{1,6}">
            <input type="number" id="diemTongKet_${dot}_1" placeholder="Nhập điểm tổng kết (0-10)" min="0" max="10" step="0.1">
            <button onclick="addSubject(${dot})">Thêm môn học</button>
            <div id="errorContainerDot_${dot}" class="error"></div>
        </div>
        <div class="nav-buttons">
            <button class="btn btn-back" onclick="prevDot(${dot})" ${dot === 2 ? 'disabled' : ''}>Quay lại</button>
            <button class="btn btn-ok" onclick="submitDot(${dot})">OK</button>
        </div>
    `;

    container.appendChild(formGroup);
}

function addSubject(dot) {
    const subjectsContainer = document.getElementById(`subjects_${dot}`);
    const subjectCount = subjectsContainer.children.length / 2 + 1;

    const inputFields = `
        <div id="subject_${dot}_${subjectCount}">
            <input type="text" id="maMon_${dot}_${subjectCount}" placeholder="Nhập mã môn học (tối đa 6 số)" maxlength="6" pattern="\\d{1,6}">
            <input type="number" id="diemTongKet_${dot}_${subjectCount}" placeholder="Nhập điểm tổng kết (0-10)" min="0" max="10" step="0.1">
            <button onclick="removeSubject(${dot}, ${subjectCount})">Xóa môn học</button>
        </div>
    `;

    subjectsContainer.insertAdjacentHTML('beforeend', inputFields);
}

function removeSubject(dot, subjectCount) {
    const subjectElement = document.getElementById(`subject_${dot}_${subjectCount}`);
    if (subjectElement) {
        subjectElement.remove();
    }
}

function submitDot(dot) {
    const subjects = [];
    const subjectsContainer = document.getElementById(`subjects_${dot}`);

    for (let i = 1; i <= subjectsContainer.children.length / 2; i++) {
        const maMonElement = document.getElementById(`maMon_${dot}_${i}`);
        const diemTongKetElement = document.getElementById(`diemTongKet_${dot}_${i}`);
        
        if (maMonElement && diemTongKetElement) {
            const maMon = maMonElement.value;
            const diemTongKet = parseFloat(diemTongKetElement.value);
            const errorContainer = document.getElementById(`errorContainerDot_${dot}`);

            if (maMon.length > 0 && maMon.length <= 6 && !isNaN(diemTongKet) && diemTongKet >= 0 && diemTongKet <= 10) {
                subjects.push({
                    MaMonHoc: maMon,
                    DiemTongKet: diemTongKet
                });
            } else {
                errorContainer.innerHTML = "Vui lòng nhập đúng mã môn học và điểm tổng kết!";
                return;
            }
        }
    }

    data[dot] = subjects;

    currentDot++;
    if (currentDot <= totalDot + 1) {
        addInputFields(currentDot);
    } else {
        document.getElementById('inputContainer').innerHTML = '';
        document.getElementById('startButton').disabled = false;
        document.getElementById('numOfDot').value = '';
        currentDot = 2;
        
        submitData();
    }
}

function prevDot(dot) {
    if (dot > 2) {
        currentDot = dot - 1;
        addInputFields(currentDot);
    }
}

async function submitData() {
    const subjects_by_dot_hoc = Object.keys(data).map(dot => ({
        DotHoc: parseInt(dot),
        subjects: data[dot]
    }));

    try {
        const response = await fetch('http://127.0.0.1:8000/predict/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ subjects_by_dot_hoc })
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error('Lỗi khi gửi dữ liệu:', response.status, errorText);
            throw new Error(`Lỗi khi gửi dữ liệu: ${response.status} - ${errorText}`);
        }

        const result = await response.json();
        displayResults(result);
    } catch (error) {
        console.error('Lỗi khi gửi dữ liệu:', error.message);
    }
}

function displayResults(result) {
    const resultContainer = document.getElementById('resultContainer');
    resultContainer.innerHTML = '';

    const table = document.createElement('table');
    table.style.width = '100%';
    table.style.borderCollapse = 'collapse';

    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    headerRow.innerHTML = `
        <th>Model</th>
        <th>Tên môn học</th>
        <th>Điểm trung bình</th>
    `;
    thead.appendChild(headerRow);
    table.appendChild(thead);

    const tbody = document.createElement('tbody');

    result.model_predict.forEach(modelPredict => {
        modelPredict.predict.forEach(predict => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${modelPredict.Model}</td>
                <td>${predict.TenMonHoc}</td>
                <td>${predict.DiemTB}</td>
            `;
            tbody.appendChild(row);
        });
    });

    table.appendChild(tbody);
    resultContainer.appendChild(table);
}
