import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix, classification_report
from typing import Dict, Any
from utils.logger import logger
import matplotlib.pyplot as plt
import seaborn as sns
import os

class ModelEvaluator:
    def __init__(self):
        pass
    
    def evaluate(self, model, X_test: np.ndarray, y_test: np.ndarray, model_type: str = "random_forest") -> Dict[str, Any]:
        """Modeli değerlendir"""
        logger.info("Model değerlendiriliyor...")
        
        # Tahminleri al
        y_pred = model.predict(X_test)
        
        # Sınıf sayısını belirle
        n_classes = len(np.unique(y_test))
        if n_classes == 2:
            avg = 'binary'
        else:
            avg = 'weighted'
        
        # Probability tahminleri (varsa)
        if hasattr(model, 'predict_proba'):
            if n_classes == 2:
                y_pred_proba = model.predict_proba(X_test)[:, 1]
            else:
                y_pred_proba = model.predict_proba(X_test)
        elif hasattr(model, 'decision_function'):
            y_pred_proba = model.decision_function(X_test)
        else:
            y_pred_proba = y_pred
        
        # Metrikleri hesapla
        metrics = {
            'accuracy': float(accuracy_score(y_test, y_pred)),
            'precision': float(precision_score(y_test, y_pred, average=avg, zero_division=0)),
            'recall': float(recall_score(y_test, y_pred, average=avg, zero_division=0)),
            'f1_score': float(f1_score(y_test, y_pred, average=avg, zero_division=0))
        }
        
        # ROC-AUC (eğer probabilistic tahmin varsa)
        try:
            if n_classes == 2:
                metrics['roc_auc'] = float(roc_auc_score(y_test, y_pred_proba))
            else:
                metrics['roc_auc'] = float(roc_auc_score(y_test, y_pred_proba, multi_class='ovr', average='weighted'))
        except:
            metrics['roc_auc'] = None
        
        # Confusion Matrix
        cm = confusion_matrix(y_test, y_pred)
        metrics['confusion_matrix'] = cm.tolist()
        
        # Classification Report
        metrics['classification_report'] = classification_report(y_test, y_pred, output_dict=True)
        
        logger.info(f"Model değerlendirme tamamlandı - Accuracy: {metrics['accuracy']:.4f}")
        return metrics
    
    def create_evaluation_plots(self, metrics: Dict[str, Any], save_path: str) -> str:
        """Değerlendirme grafiklerini oluştur"""
        plt.figure(figsize=(12, 8))
        
        # Confusion Matrix
        plt.subplot(2, 2, 1)
        cm = np.array(metrics['confusion_matrix'])
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
        plt.title('Confusion Matrix')
        plt.xlabel('Predicted')
        plt.ylabel('Actual')
        
        # Metrics Bar Plot
        plt.subplot(2, 2, 2)
        metric_names = ['Accuracy', 'Precision', 'Recall', 'F1-Score']
        metric_values = [
            metrics['accuracy'],
            metrics['precision'], 
            metrics['recall'],
            metrics['f1_score']
        ]
        plt.bar(metric_names, metric_values)
        plt.title('Model Metrics')
        plt.ylabel('Score')
        plt.ylim(0, 1)
        
        # ROC AUC (if available)
        if metrics.get('roc_auc'):
            plt.subplot(2, 2, 3)
            plt.text(0.5, 0.5, f"ROC-AUC: {metrics['roc_auc']:.4f}", 
                    horizontalalignment='center', verticalalignment='center',
                    fontsize=16, transform=plt.gca().transAxes)
            plt.title('ROC-AUC Score')
            plt.axis('off')
        
        plt.tight_layout()
        plot_path = os.path.join(save_path, 'evaluation_plots.png')
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Değerlendirme grafikleri kaydedildi: {plot_path}")
        return plot_path
