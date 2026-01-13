sap.ui.define([
    "sap/ui/core/UIComponent",
    "sap/ui/model/json/JSONModel"
], function (UIComponent, JSONModel) {
    "use strict";

    return UIComponent.extend("invoice.ocr.app.Component", {
        metadata: {
            manifest: "json"
        },

        /**
         * The component is initialized by UI5 automatically during the startup of the app and calls the init method once.
         * @public
         * @override
         */
        init: function () {
            // Call the base component's init function
            UIComponent.prototype.init.apply(this, arguments);

            // Create invoice data model
            var oInvoiceModel = new JSONModel({
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
            this.setModel(oInvoiceModel, "invoiceData");

            // Create view model for UI state
            var oViewModel = new JSONModel({
                busy: false,
                hasError: false,
                errorMessage: "",
                maxFileSizeMB: 10
            });
            this.setModel(oViewModel, "viewModel");
        }
    });
});
