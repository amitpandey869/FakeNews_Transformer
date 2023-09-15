# -*- coding: utf-8 -*-
"""FakeNews1(BERT).ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1TU9Qb29tmLol5eRb06-OJv9Ev7bpHHDn
"""

pip install transformers

pip install pandas

pip install numpy

pip install torch

pip install scikit-learn

pip install tqdm

import numpy as np
import pandas as pd
import torch
from transformers import BertTokenizer, BertForSequenceClassification, AdamW, get_linear_schedule_with_warmup
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from torch.utils.data import DataLoader, TensorDataset
from tqdm import tqdm

fake_df = pd.read_csv(r'C:\Users\amitp\OneDrive\Desktop\Fake.csv')
true_df = pd.read_csv(r'C:\Users\amitp\OneDrive\Desktop\True.csv')

fake_df['label'] = 1
true_df['label'] = 0
combined_df = pd.concat([fake_df, true_df], ignore_index=True)

combined_df = combined_df.sample(frac=1).reset_index(drop=True)

tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')

def tokenize_and_prepare_data(dataframe, max_length=128, batch_size=32):
    input_ids = []
    attention_masks = []
    labels = []

    for idx, row in tqdm(dataframe.iterrows(), total=len(dataframe)):
        text = row['text']
        label = row['label']

        encoded_text = tokenizer.encode_plus(
            text,
            add_special_tokens=True,
            max_length=max_length,
            padding='max_length',
            return_tensors='pt',
            truncation=True
        )

        input_ids.append(encoded_text['input_ids'])
        attention_masks.append(encoded_text['attention_mask'])
        labels.append(label)

    input_ids = torch.cat(input_ids, dim=0)
    attention_masks = torch.cat(attention_masks, dim=0)
    labels = torch.tensor(labels)

    dataset = TensorDataset(input_ids, attention_masks, labels)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    return dataloader

train_df, test_df = train_test_split(combined_df, test_size=0.2, random_state=42)

train_dataloader = tokenize_and_prepare_data(train_df)
test_dataloader = tokenize_and_prepare_data(test_df)

model = BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels=2)

optimizer = AdamW(model.parameters(), lr=2e-5, eps=1e-8)
scheduler = get_linear_schedule_with_warmup(
    optimizer,
    num_warmup_steps=0,
    num_training_steps=len(train_dataloader) * 2
)


device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model.to(device)

epochs = 3
for epoch in range(epochs):
    model.train()
    total_loss = 0

    for batch in tqdm(train_dataloader, desc=f'Epoch {epoch + 1}'):
        input_ids, attention_mask, labels = batch
        input_ids = input_ids.to(device)
        attention_mask = attention_mask.to(device)
        labels = labels.to(device)

        model.zero_grad()

        outputs = model(input_ids, attention_mask=attention_mask, labels=labels)
        loss = outputs.loss
        total_loss += loss.item()

        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)

        optimizer.step()
        scheduler.step()

    avg_train_loss = total_loss / len(train_dataloader)
    print(f'Average training loss: {avg_train_loss}')


model.eval()
eval_predictions = []
eval_labels = []

for batch in tqdm(test_dataloader, desc='Evaluating'):
    input_ids, attention_mask, labels = batch
    input_ids = input_ids.to(device)
    attention_mask = attention_mask.to(device)
    labels = labels.to(device)

    with torch.no_grad():
        outputs = model(input_ids, attention_mask=attention_mask)

    logits = outputs.logits
    predictions = torch.argmax(logits, dim=1).tolist()
    eval_predictions.extend(predictions)
    eval_labels.extend(labels.tolist())

accuracy = accuracy_score(eval_labels, eval_predictions)
print(f'Accuracy: {accuracy}')
print(classification_report(eval_labels, eval_predictions, target_names=['Real', 'Fake']))

