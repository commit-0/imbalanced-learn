"""SMOTE variant applying some filtering before the generation process."""
import numbers
import warnings
import numpy as np
from scipy import sparse
from sklearn.base import clone
from sklearn.svm import SVC
from sklearn.utils import _safe_indexing, check_random_state
from ...utils import Substitution, check_neighbors_object
from ...utils._docstring import _n_jobs_docstring, _random_state_docstring
from ...utils._param_validation import HasMethods, Interval, StrOptions
from ..base import BaseOverSampler
from .base import BaseSMOTE

@Substitution(sampling_strategy=BaseOverSampler._sampling_strategy_docstring, n_jobs=_n_jobs_docstring, random_state=_random_state_docstring)
class BorderlineSMOTE(BaseSMOTE):
    """Over-sampling using Borderline SMOTE.

    This algorithm is a variant of the original SMOTE algorithm proposed in
    [2]_. Borderline samples will be detected and used to generate new
    synthetic samples.

    Read more in the :ref:`User Guide <smote_adasyn>`.

    .. versionadded:: 0.4

    Parameters
    ----------
    {sampling_strategy}

    {random_state}

    k_neighbors : int or object, default=5
        The nearest neighbors used to define the neighborhood of samples to use
        to generate the synthetic samples. You can pass:

        - an `int` corresponding to the number of neighbors to use. A
          `~sklearn.neighbors.NearestNeighbors` instance will be fitted in this
          case.
        - an instance of a compatible nearest neighbors algorithm that should
          implement both methods `kneighbors` and `kneighbors_graph`. For
          instance, it could correspond to a
          :class:`~sklearn.neighbors.NearestNeighbors` but could be extended to
          any compatible class.

    {n_jobs}

        .. deprecated:: 0.10
           `n_jobs` has been deprecated in 0.10 and will be removed in 0.12.
           It was previously used to set `n_jobs` of nearest neighbors
           algorithm. From now on, you can pass an estimator where `n_jobs` is
           already set instead.

    m_neighbors : int or object, default=10
        The nearest neighbors used to determine if a minority sample is in
        "danger". You can pass:

        - an `int` corresponding to the number of neighbors to use. A
          `~sklearn.neighbors.NearestNeighbors` instance will be fitted in this
          case.
        - an instance of a compatible nearest neighbors algorithm that should
          implement both methods `kneighbors` and `kneighbors_graph`. For
          instance, it could correspond to a
          :class:`~sklearn.neighbors.NearestNeighbors` but could be extended to
          any compatible class.

    kind : {{"borderline-1", "borderline-2"}}, default='borderline-1'
        The type of SMOTE algorithm to use one of the following options:
        ``'borderline-1'``, ``'borderline-2'``.

    Attributes
    ----------
    sampling_strategy_ : dict
        Dictionary containing the information to sample the dataset. The keys
        corresponds to the class labels from which to sample and the values
        are the number of samples to sample.

    nn_k_ : estimator object
        Validated k-nearest neighbours created from the `k_neighbors` parameter.

    nn_m_ : estimator object
        Validated m-nearest neighbours created from the `m_neighbors` parameter.

    in_danger_indices : dict of ndarray
        Dictionary containing the indices of the samples considered in danger that
        are used to generate new synthetic samples. The keys corresponds to the class
        label.

    n_features_in_ : int
        Number of features in the input dataset.

        .. versionadded:: 0.9

    feature_names_in_ : ndarray of shape (`n_features_in_`,)
        Names of features seen during `fit`. Defined only when `X` has feature
        names that are all strings.

        .. versionadded:: 0.10

    See Also
    --------
    SMOTE : Over-sample using SMOTE.

    SMOTENC : Over-sample using SMOTE for continuous and categorical features.

    SVMSMOTE : Over-sample using SVM-SMOTE variant.

    ADASYN : Over-sample using ADASYN.

    KMeansSMOTE : Over-sample applying a clustering before to oversample using
        SMOTE.

    Notes
    -----
    See the original papers: [2]_ for more details.

    Supports multi-class resampling. A one-vs.-rest scheme is used as
    originally proposed in [1]_.

    References
    ----------
    .. [1] N. V. Chawla, K. W. Bowyer, L. O.Hall, W. P. Kegelmeyer, "SMOTE:
       synthetic minority over-sampling technique," Journal of artificial
       intelligence research, 321-357, 2002.

    .. [2] H. Han, W. Wen-Yuan, M. Bing-Huan, "Borderline-SMOTE: a new
       over-sampling method in imbalanced data sets learning," Advances in
       intelligent computing, 878-887, 2005.

    Examples
    --------
    >>> from collections import Counter
    >>> from sklearn.datasets import make_classification
    >>> from imblearn.over_sampling import BorderlineSMOTE
    >>> X, y = make_classification(n_classes=2, class_sep=2,
    ... weights=[0.1, 0.9], n_informative=3, n_redundant=1, flip_y=0,
    ... n_features=20, n_clusters_per_class=1, n_samples=1000, random_state=10)
    >>> print('Original dataset shape %s' % Counter(y))
    Original dataset shape Counter({{1: 900, 0: 100}})
    >>> sm = BorderlineSMOTE(random_state=42)
    >>> X_res, y_res = sm.fit_resample(X, y)
    >>> print('Resampled dataset shape %s' % Counter(y_res))
    Resampled dataset shape Counter({{0: 900, 1: 900}})
    """
    _parameter_constraints: dict = {**BaseSMOTE._parameter_constraints, 'm_neighbors': [Interval(numbers.Integral, 1, None, closed='left'), HasMethods(['kneighbors', 'kneighbors_graph'])], 'kind': [StrOptions({'borderline-1', 'borderline-2'})]}

    def __init__(self, *, sampling_strategy='auto', random_state=None, k_neighbors=5, n_jobs=None, m_neighbors=10, kind='borderline-1'):
        super().__init__(sampling_strategy=sampling_strategy, random_state=random_state, k_neighbors=k_neighbors, n_jobs=n_jobs)
        self.m_neighbors = m_neighbors
        self.kind = kind

@Substitution(sampling_strategy=BaseOverSampler._sampling_strategy_docstring, n_jobs=_n_jobs_docstring, random_state=_random_state_docstring)
class SVMSMOTE(BaseSMOTE):
    """Over-sampling using SVM-SMOTE.

    Variant of SMOTE algorithm which use an SVM algorithm to detect sample to
    use for generating new synthetic samples as proposed in [2]_.

    Read more in the :ref:`User Guide <smote_adasyn>`.

    .. versionadded:: 0.4

    Parameters
    ----------
    {sampling_strategy}

    {random_state}

    k_neighbors : int or object, default=5
        The nearest neighbors used to define the neighborhood of samples to use
        to generate the synthetic samples. You can pass:

        - an `int` corresponding to the number of neighbors to use. A
          `~sklearn.neighbors.NearestNeighbors` instance will be fitted in this
          case.
        - an instance of a compatible nearest neighbors algorithm that should
          implement both methods `kneighbors` and `kneighbors_graph`. For
          instance, it could correspond to a
          :class:`~sklearn.neighbors.NearestNeighbors` but could be extended to
          any compatible class.

    {n_jobs}

        .. deprecated:: 0.10
           `n_jobs` has been deprecated in 0.10 and will be removed in 0.12.
           It was previously used to set `n_jobs` of nearest neighbors
           algorithm. From now on, you can pass an estimator where `n_jobs` is
           already set instead.

    m_neighbors : int or object, default=10
        The nearest neighbors used to determine if a minority sample is in
        "danger". You can pass:

        - an `int` corresponding to the number of neighbors to use. A
          `~sklearn.neighbors.NearestNeighbors` instance will be fitted in this
          case.
        - an instance of a compatible nearest neighbors algorithm that should
          implement both methods `kneighbors` and `kneighbors_graph`. For
          instance, it could correspond to a
          :class:`~sklearn.neighbors.NearestNeighbors` but could be extended to
          any compatible class.

    svm_estimator : estimator object, default=SVC()
        A parametrized :class:`~sklearn.svm.SVC` classifier can be passed.
        A scikit-learn compatible estimator can be passed but it is required
        to expose a `support_` fitted attribute.

    out_step : float, default=0.5
        Step size when extrapolating.

    Attributes
    ----------
    sampling_strategy_ : dict
        Dictionary containing the information to sample the dataset. The keys
        corresponds to the class labels from which to sample and the values
        are the number of samples to sample.

    nn_k_ : estimator object
        Validated k-nearest neighbours created from the `k_neighbors` parameter.

    nn_m_ : estimator object
        Validated m-nearest neighbours created from the `m_neighbors` parameter.

    svm_estimator_ : estimator object
        The validated SVM classifier used to detect samples from which to
        generate new synthetic samples.

    n_features_in_ : int
        Number of features in the input dataset.

        .. versionadded:: 0.9

    feature_names_in_ : ndarray of shape (`n_features_in_`,)
        Names of features seen during `fit`. Defined only when `X` has feature
        names that are all strings.

        .. versionadded:: 0.10

    See Also
    --------
    SMOTE : Over-sample using SMOTE.

    SMOTENC : Over-sample using SMOTE for continuous and categorical features.

    SMOTEN : Over-sample using the SMOTE variant specifically for categorical
        features only.

    BorderlineSMOTE : Over-sample using Borderline-SMOTE.

    ADASYN : Over-sample using ADASYN.

    KMeansSMOTE : Over-sample applying a clustering before to oversample using
        SMOTE.

    Notes
    -----
    See the original papers: [2]_ for more details.

    Supports multi-class resampling. A one-vs.-rest scheme is used as
    originally proposed in [1]_.

    References
    ----------
    .. [1] N. V. Chawla, K. W. Bowyer, L. O.Hall, W. P. Kegelmeyer, "SMOTE:
       synthetic minority over-sampling technique," Journal of artificial
       intelligence research, 321-357, 2002.

    .. [2] H. M. Nguyen, E. W. Cooper, K. Kamei, "Borderline over-sampling for
       imbalanced data classification," International Journal of Knowledge
       Engineering and Soft Data Paradigms, 3(1), pp.4-21, 2009.

    Examples
    --------
    >>> from collections import Counter
    >>> from sklearn.datasets import make_classification
    >>> from imblearn.over_sampling import SVMSMOTE
    >>> X, y = make_classification(n_classes=2, class_sep=2,
    ... weights=[0.1, 0.9], n_informative=3, n_redundant=1, flip_y=0,
    ... n_features=20, n_clusters_per_class=1, n_samples=1000, random_state=10)
    >>> print('Original dataset shape %s' % Counter(y))
    Original dataset shape Counter({{1: 900, 0: 100}})
    >>> sm = SVMSMOTE(random_state=42)
    >>> X_res, y_res = sm.fit_resample(X, y)
    >>> print('Resampled dataset shape %s' % Counter(y_res))
    Resampled dataset shape Counter({{0: 900, 1: 900}})
    """
    _parameter_constraints: dict = {**BaseSMOTE._parameter_constraints, 'm_neighbors': [Interval(numbers.Integral, 1, None, closed='left'), HasMethods(['kneighbors', 'kneighbors_graph'])], 'svm_estimator': [HasMethods(['fit', 'predict']), None], 'out_step': [Interval(numbers.Real, 0, 1, closed='both')]}

    def __init__(self, *, sampling_strategy='auto', random_state=None, k_neighbors=5, n_jobs=None, m_neighbors=10, svm_estimator=None, out_step=0.5):
        super().__init__(sampling_strategy=sampling_strategy, random_state=random_state, k_neighbors=k_neighbors, n_jobs=n_jobs)
        self.m_neighbors = m_neighbors
        self.svm_estimator = svm_estimator
        self.out_step = out_step