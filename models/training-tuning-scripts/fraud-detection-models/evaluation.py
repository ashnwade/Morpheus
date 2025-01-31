# SPDX-FileCopyrightText: Copyright (c) 2022-2023, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from matplotlib import pyplot
from sklearn.metrics import average_precision_score
from sklearn.metrics import f1_score
from sklearn.metrics import precision_recall_curve
from sklearn.metrics import precision_recall_fscore_support
from sklearn.metrics import roc_auc_score
from sklearn.metrics import roc_curve


class Evaluation:
    """
    This class initializes the evaluation of a classification model.

    Parameters
    ----------
    probabilities : iterable
        The predicted probabilities per class for the classification model.
    labels : iterable
        The labels corresponding with the predicted probabilities.
    name : str
        The name of the used configuration
    """

    def __init__(self, probabilities, labels, name):

        self.probabilities = probabilities
        self.labels = labels
        self.name = name

    def pr_curve(self):
        """
        This function plots the precision recall curve for the used classification model and a majority classifier.

        """
        probs = self.probabilities[:, 1]
        precision, recall, _ = precision_recall_curve(self.labels, probs)
        pyplot.plot(recall, precision, label=self.name)
        # axis labels
        pyplot.xlabel('Recall')
        pyplot.ylabel('Precision')
        # show the legend
        pyplot.legend()

        print('Average precision-recall score for ',
              self.name,
              ' configuration XGBoost: {0:0.10f}'.format(average_precision_score(self.labels, probs)))

    def roc_curve(self, model_name='XGBoost'):
        """
        This function plots the precision recall curve for the used classification model and a majority classifier.

        """
        probs = self.probabilities[:, 1]
        fpr, tpr, _ = roc_curve(self.labels, probs)
        auc = round(roc_auc_score(self.labels, probs), 3)
        pyplot.plot(fpr, tpr, label=self.name + str(auc))
        # axis labels
        pyplot.xlabel('FPR')
        pyplot.ylabel('TPR')
        # show the legend
        pyplot.legend()

        print('ROC score for ', self.name, ' configuration : {0:0.10f}'.format(auc))
        return auc

    def f1_ap_rec(self):

        probs = self.probabilities[:, 1] >= 0.5
        prec, rec, f1, num = precision_recall_fscore_support(self.labels, probs, average=None)

        print("Precision:%.3f \nRecall:%.3f \nF1 Score:%.3f" % (prec[1], rec[1], f1[1]))
        micro_f1 = f1_score(self.labels, probs, average='micro')
        print("Micro-Average F1 Score:", micro_f1)
        # return micro_f1
