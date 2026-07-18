import sklearn
import sklearn.ensemble as e
print(sklearn.__version__)
print([x for x in dir(e) if 'GradientBoosting' in x])
try:
 from sklearn.ensemble._hist_gradient_boosting.gradient_boosting import HistGradientBoostingClassifier
 print('private_hgb_classifier=yes')
except Exception as exc:
 print('private_hgb_classifier=no',repr(exc))
