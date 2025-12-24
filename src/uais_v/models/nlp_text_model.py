"""DistilBERT text classifier fine-tuning scaffold."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

import torch
from torch import nn
from transformers import AutoConfig, AutoModel, AutoTokenizer, DistilBertConfig


@dataclass
class NLPTextConfig:
    model_name: str = "distilbert-base-uncased"
    num_labels: int = 2
    max_length: int = 128


class DistilBERTClassifier(nn.Module):
    def __init__(
        self,
        model_name: str = "distilbert-base-uncased",
        num_labels: int = 2,
        *,
        from_scratch: bool = False,
        local_files_only: bool | None = None,
    ):
        super().__init__()
        if local_files_only is None:
            local_files_only = os.getenv("TRANSFORMERS_OFFLINE", "").strip() in {
                "1",
                "true",
                "yes",
                "on",
            }

        if from_scratch:
            try:
                self.config = AutoConfig.from_pretrained(
                    model_name,
                    num_labels=num_labels,
                    local_files_only=bool(local_files_only),
                )
            except Exception:
                self.config = DistilBertConfig(num_labels=num_labels)
            self.bert = AutoModel.from_config(self.config)
        else:
            self.config = AutoConfig.from_pretrained(
                model_name,
                num_labels=num_labels,
                local_files_only=bool(local_files_only),
            )
            self.bert = AutoModel.from_pretrained(
                model_name,
                config=self.config,
                local_files_only=bool(local_files_only),
            )
        hidden = self.config.hidden_size
        self.classifier = nn.Linear(hidden, num_labels if num_labels > 1 else 1)

    def forward(self, input_ids, attention_mask):
        out = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        pooled = out.last_hidden_state[:, 0]
        logits = self.classifier(pooled)
        return logits


def get_tokenizer(
    model_name: str = "distilbert-base-uncased", *, local_files_only: bool | None = None
):
    if local_files_only is None:
        local_files_only = os.getenv("TRANSFORMERS_OFFLINE", "").strip() in {
            "1",
            "true",
            "yes",
            "on",
        }
    return AutoTokenizer.from_pretrained(model_name, local_files_only=bool(local_files_only))


__all__ = ["DistilBERTClassifier", "NLPTextConfig", "get_tokenizer"]
