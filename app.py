from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
import pandas as pd
import joblib
from tensorflow.keras.models import load_model
from sklearn.preprocessing import LabelEncoder
# from processing_data import process_data

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],  # Add your frontend URL here
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# import tensorflow as tf

# print(f"TensorFlow Version: {tf.__version__}")
# # Load the trained models and label encoder
# lstm_model = load_model("lstm_2_model.h5")
# gru_model = load_model("gru_2_model.h5")

# label_encoder = joblib.load("label_encoder.pkl")

# Temporary storage for subjects
# students_data = {}
def process_data(data):
    # label_subject = LabelEncoder()
    # data['MaMonHoc'] = label_subject.fit_transform(data['MaMonHoc'])
    # print(len(np.unique(data['MaMonHoc'])))
    lst_sv = data['IDSinhVien'].values
    lst_sv = set(lst_sv)
    lst_sv = list(lst_sv)
    X = []
    Y = []
    for sv in lst_sv:
        data_Sv = data[data['IDSinhVien'] == sv][['DotHoc','MaMonHoc','DiemTongKet']]
        data_Sv.head()
        data_Sv = np.array(data_Sv)
        label = data[data['IDSinhVien'] == sv][['MaMonHoc']]
        label = np.array(label)
        i = 0
        while( i < len(data_Sv)-1):
            X_one = np.zeros((15,3))
            
            if data_Sv[i][0] == data_Sv[i+1][0] and data_Sv[i][0] != 2:
                # X.append(X[-1])
                # Y.append(label[i+1])
                i += 1
            elif data_Sv[i][0] == data_Sv[i+1][0] and data_Sv[i][0] == 2:
                i += 1
            else:
                for j in range(i+1):
                    X_one[j] = data_Sv[j]
                X.append(X_one)
                Y.append(label[i+1])
                i += 1
    X = np.array(X)
    y = np.array(Y)
    
    
    return X, y

class Subject(BaseModel):
    MaMonHoc: str
    DiemTongKet: float

class DotHocSubjects(BaseModel):
    DotHoc: int
    subjects: list[Subject]

class repost_sub(BaseModel):
    TenMonHoc : str
    DiemTB : float

class AllSubjects(BaseModel):
    subjects_by_dot_hoc: list[DotHocSubjects]
    
class repost_model(BaseModel):
    Model : str
    predict : list[repost_sub]
    
class repost_api(BaseModel):
    message : str
    model_predict : list[repost_model]

# @app.post("/add_all_subjects/")
# async def add_all_subjects(data: AllSubjects):
#     # Store all subjects from DotHoc 2 onwards
#     for dot_hoc_data in data.subjects_by_dot_hoc:
#         if dot_hoc_data.DotHoc < 2:
#             raise HTTPException(status_code=400, detail="Chỉ nhập từ đợt học thứ 2 trở đi.")
        
#         students_data = {}
#         # Add subjects for each DotHoc
#         if dot_hoc_data.DotHoc not in students_data:
#             students_data[dot_hoc_data.DotHoc] = []

#         for subject in dot_hoc_data.subjects:
#             students_data[dot_hoc_data.DotHoc].append({
#                 "DotHoc": dot_hoc_data.DotHoc,
#                 "MaMonHoc": subject.MaMonHoc,
#                 "DiemTongKet": subject.DiemTongKet
#             })

#     return {
#         "message": "Dữ liệu các đợt học đã được thêm thành công.",
#         "all_subjects": students_data
#     }

@app.post("/predict")
async def predict(data: AllSubjects):
    lstm_model = load_model("lstm_2_model.h5")
    gru_model = load_model("gru_2_model.h5")
    
    df = pd.read_csv('data_deep_clean_v6.csv')
    X, y = process_data(df)
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(y)
    
    students_data = {}
    for dot_hoc_data in data.subjects_by_dot_hoc:
        if dot_hoc_data.DotHoc < 2:
            raise HTTPException(status_code=400, detail="Chỉ nhập từ đợt học thứ 2 trở đi.")
        
        
        # Add subjects for each DotHoc
        if dot_hoc_data.DotHoc not in students_data:
            students_data[dot_hoc_data.DotHoc] = []

        for subject in dot_hoc_data.subjects:
            students_data[dot_hoc_data.DotHoc].append({
                "DotHoc": dot_hoc_data.DotHoc,
                "MaMonHoc": subject.MaMonHoc,
                "DiemTongKet": subject.DiemTongKet
            })
            
    if len(students_data) == 0:
        raise HTTPException(status_code=400, detail="Không có môn học nào để dự đoán.")

    # Combine all subjects data
    all_subjects = []
    for dot_hoc in sorted(students_data.keys()):
        all_subjects.extend(students_data[dot_hoc])

    subject = pd.DataFrame(all_subjects)
    input = np.zeros((15,3))
    for i in range(subject.shape[0]):
        input[i] = subject.iloc[i].values
    input= input.reshape(1, 15, 3)
    
    print(input)
    # Predict using both models
    lstm_predictions = lstm_model.predict(input)
    gru_predictions = gru_model.predict(input)
    sorted_indices = np.argsort(lstm_predictions, axis=1)[:, ::-1]
    # Lấy chỉ số của 4 giá trị lớn nhất trong mỗi hàng
    y_lstm = sorted_indices[:, :4]
    
    # lstm_monhoc = np.argmax(lstm_predictions, axis=1)
    sorted_indices = np.argsort(gru_predictions, axis=1)[:, ::-1]
    y_gru = sorted_indices[:, :4]
    # Map predictions back to MaMonHoc
    
    lstm_predicted_mamons = label_encoder.inverse_transform(y_lstm[0])
    gru_predicted_mamons = label_encoder.inverse_transform(y_gru[0])
    
    lstm_reponse = []
    for mamon in lstm_predicted_mamons:
        a = df[df['MaMonHoc'] == mamon].iloc[0]
        b = repost_sub(TenMonHoc=a.TenMonHoc, DiemTB=a.DiemTBMon)
        lstm_reponse.append(b)
        
    gru_reponse = []
    for mamon in gru_predicted_mamons:
        a = df[df['MaMonHoc'] == mamon].iloc[0]
        b = repost_sub(TenMonHoc=a.TenMonHoc, DiemTB=a.DiemTBMon)
        gru_reponse.append(b)
    
    api_lstm_response = repost_model(Model = "LSTM", predict = lstm_reponse)
    api_gru_response = repost_model(Model = "GRU", predict = gru_reponse)
    list_predict_model = list([api_lstm_response,api_gru_response])
    api_response = repost_api(message = "complete api", model_predict = list_predict_model)
    return api_response        


