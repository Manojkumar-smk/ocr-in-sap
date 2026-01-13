sap.ui.define([
    "sap/ui/core/mvc/Controller",
    "sap/ui/model/json/JSONModel",
    "sap/m/MessageBox",
    "sap/m/MessageToast"
], function (Controller, JSONModel, MessageBox, MessageToast) {
    "use strict";

    return Controller.extend("invoice.ocr.app.controller.InvoiceUpload", {
        /**
         * Called when the controller is instantiated.
         * @public
         */
        onInit: function () {
            // Get models
            this.oInvoiceModel = this.getOwnerComponent().getModel("invoiceData");
            this.oViewModel = this.getOwnerComponent().getModel("viewModel");

            // Set API base URL from manifest
            var oManifest = this.getOwnerComponent().getManifestObject();
            var sApiUrl = oManifest.getEntry("/sap.app/dataSources/invoiceAPI/uri");
            this.sApiBaseUrl = sApiUrl || "http://localhost:8000/api/v1/";
        },

        /**
         * Event handler for file selection change
         * @param {sap.ui.base.Event} oEvent - The file change event
         * @public
         */
        onFileChange: function (oEvent) {
            var oFileUploader = this.byId("fileUploader");
            var sFileName = oEvent.getParameter("newValue");

            if (sFileName) {
                // Validate file extension
                if (!sFileName.toLowerCase().endsWith(".pdf")) {
                    MessageBox.error("Invalid file type. Please select a PDF file.");
                    oFileUploader.clear();
                    return;
                }

                MessageToast.show("File selected: " + sFileName);
            }
        },

        /**
         * Event handler for upload button press
         * @public
         */
        onUploadPress: function () {
            var oFileUploader = this.byId("fileUploader");
            var sFileName = oFileUploader.getValue();

            // Validate file selection
            if (!sFileName) {
                MessageBox.warning("Please select a PDF file to upload.");
                return;
            }

            // Get the file
            var oDomRef = oFileUploader.getFocusDomRef();
            var oFile = oDomRef ? oDomRef.files[0] : null;

            if (!oFile) {
                MessageBox.error("Unable to read the selected file.");
                return;
            }

            // Validate file size
            var nFileSizeMB = oFile.size / (1024 * 1024);
            var nMaxSizeMB = this.oViewModel.getProperty("/maxFileSizeMB");

            if (nFileSizeMB > nMaxSizeMB) {
                MessageBox.error("File size exceeds the maximum allowed size of " + nMaxSizeMB + " MB.");
                return;
            }

            // Upload the file
            this._uploadFile(oFile);
        },

        /**
         * Upload file to backend API
         * @param {File} oFile - The file to upload
         * @private
         */
        _uploadFile: function (oFile) {
            // Show busy indicator
            this.oViewModel.setProperty("/busy", true);
            this.oViewModel.setProperty("/hasError", false);
            this.oInvoiceModel.setProperty("/showResults", false);

            // Create FormData
            var oFormData = new FormData();
            oFormData.append("file", oFile);

            // Upload endpoint
            var sUploadUrl = this.sApiBaseUrl + "invoices/upload";

            // Make the request
            fetch(sUploadUrl, {
                method: "POST",
                body: oFormData
            })
            .then(function (response) {
                if (!response.ok) {
                    return response.json().then(function (errorData) {
                        throw new Error(errorData.detail || "Upload failed");
                    });
                }
                return response.json();
            })
            .then(this._handleUploadSuccess.bind(this))
            .catch(this._handleUploadError.bind(this))
            .finally(function () {
                this.oViewModel.setProperty("/busy", false);
            }.bind(this));
        },

        /**
         * Handle successful upload
         * @param {object} oData - Response data from API
         * @private
         */
        _handleUploadSuccess: function (oData) {
            // Update invoice model
            this.oInvoiceModel.setData({
                invoiceId: oData.invoice_id,
                invoiceNumber: oData.invoice_number,
                vendorName: oData.vendor_name,
                fileName: oData.file_name,
                fileSizeKb: oData.file_size_kb,
                confidenceScore: oData.confidence_score,
                status: oData.status,
                message: oData.message,
                timestamp: oData.timestamp,
                showResults: true
            });

            // Show success message
            MessageBox.success("Invoice processed successfully!\n\nInvoice Number: " + oData.invoice_number + "\nVendor: " + oData.vendor_name);

            // Clear file uploader
            this.byId("fileUploader").clear();
        },

        /**
         * Handle upload error
         * @param {Error} oError - Error object
         * @private
         */
        _handleUploadError: function (oError) {
            var sErrorMessage = oError.message || "An error occurred during upload. Please try again.";

            // Update view model
            this.oViewModel.setProperty("/hasError", true);
            this.oViewModel.setProperty("/errorMessage", sErrorMessage);

            // Show error message
            MessageBox.error("Upload failed: " + sErrorMessage);
        },

        /**
         * Event handler for clear button press
         * @public
         */
        onClearPress: function () {
            // Clear file uploader
            this.byId("fileUploader").clear();

            // Reset models
            this.oInvoiceModel.setData({
                invoiceId: null,
                invoiceNumber: "",
                vendorName: "",
                fileName: "",
                fileSizeKb: 0,
                confidenceScore: 0,
                status: "",
                message: "",
                timestamp: null,
                showResults: false
            });

            this.oViewModel.setProperty("/hasError", false);
            this.oViewModel.setProperty("/errorMessage", "");

            MessageToast.show("Form cleared");
        },

        /**
         * Event handler for closing error message
         * @public
         */
        onCloseError: function () {
            this.oViewModel.setProperty("/hasError", false);
            this.oViewModel.setProperty("/errorMessage", "");
        }
    });
});
