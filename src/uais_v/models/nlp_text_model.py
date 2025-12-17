"""DistilBERT text classifier fine-tuning scaffold."""
from dataclasses import dataclass
from typing import Optional

import torch
from torch import nn
from transformers import AutoConfig, AutoModel, AutoTokenizer


@dataclass
class NLPTextConfig:
    model_name: str = "distilbert-base-uncased"
    num_labels: int = 2
    max_length: int = 128


class DistilBERTClassifier(nn.Module):
    def __init__(self, model_name: str = "distilbert-base-uncased", num_labels: int = 2):
        super().__init__()
        self.config = AutoConfig.from_pretrained(model_name, num_labels=num_labels)
        self.bert = AutoModel.from_pretrained(model_name, config=self.config)
        hidden = self.config.hidden_size
        self.classifier = nn.Linear(hidden, num_labels if num_labels > 1 else 1)

    def forward(self, input_ids, attention_mask):
        out = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        pooled = out.last_hidden_state[:, 0]
        logits = self.classifier(pooled)
        return logits


def get_tokenizer(model_name: str = "distilbert-base-uncased"):
    return AutoTokenizer.from_pretrained(model_name)


__all__ = ["DistilBERTClassifier", "NLPTextConfig", "get_tokenizer"]
