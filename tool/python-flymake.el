;;; Copyright (c) 2014 MIT Probabilistic Computing Project.
;;;
;;; This file is part of Venture.
;;;
;;; Venture is free software: you can redistribute it and/or modify
;;; it under the terms of the GNU General Public License as published by
;;; the Free Software Foundation, either version 3 of the License, or
;;; (at your option) any later version.
;;;
;;; Venture is distributed in the hope that it will be useful,
;;; but WITHOUT ANY WARRANTY; without even the implied warranty of
;;; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
;;; GNU General Public License for more details.
;;;
;;; You should have received a copy of the GNU General Public License
;;; along with Venture.  If not, see <http://www.gnu.org/licenses/>.

;;; N.B. venture-epylint.py or a symlink thereto needs to be on your
;;; $PATH somewhere for flymake to work right.
;;; Of course, pylint also needs to be installed.

;; (setq python-indent 2)
;; (add-hook 'python-mode-hook 'python-guess-indent)

;; Set Flymake as a minor mode for Python
(add-hook 'python-mode-hook '(lambda () (flymake-mode)))

;; Configure Flymake wait a bit longer after edits before starting
(setq-default flymake-no-changes-timeout '1)

;; Keymaps to navigate to Flymake errors in Python mode
(add-hook 'python-mode-hook '(lambda () (define-key python-mode-map "\C-cn" 'flymake-goto-next-error)))
(add-hook 'python-mode-hook '(lambda () (define-key python-mode-map "\C-cp" 'flymake-goto-prev-error)))

;; To avoid having to mouse hover for a Flymake error message, these
;; functions make flymake error messages appear in the minibuffer
(defun show-fly-err-at-point ()
  "If the cursor is sitting on a flymake error, display the message in the minibuffer"
  (require 'cl)
  (interactive)
  (let ((line-no (line-number-at-pos)))
    (dolist (elem flymake-err-info)
      (if (eq (car elem) line-no)
      (let ((err (car (second elem))))
        (message "%s" (flymake-ler-text err)))))))

(add-hook 'python-mode-hook '(lambda () (add-hook 'post-command-hook 'show-fly-err-at-point)))

;; Configure flymake for Python
(when (load "flymake" t)
  (defun flymake-pylint-init ()
    (let* ((temp-file (flymake-init-create-temp-buffer-copy
                       'flymake-create-temp-inplace))
           (local-file (file-relative-name
                        temp-file
                        (file-name-directory buffer-file-name))))
      (list "venture-epylint.py" (list local-file))))
  (add-to-list 'flymake-allowed-file-name-masks
               '("\\.py\\'" flymake-pylint-init)))
