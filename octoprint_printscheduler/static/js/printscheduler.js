/*
 * View model for Print Scheduler
 *
 * Author: jneilliii
 * License: MIT
 */
$(function() {
    function PrintschedulerViewModel(parameters) {
        var self = this;

        self.settingsViewModel = parameters[0];
		self.filesViewModel = parameters[1];

		self.needs_saving = ko.observable(false);
		self.start_at_changed_for = ko.observableArray([]);
		self.theme = ko.observable('default');

		self.onBeforeBinding = function() {
		    $.datetimepicker.setDateFormatter('moment');
        };

		self.onAllBound = function(data) {
		    self.needs_saving(false);
        };

		self.start_at_changed = function(data){
		    self.needs_saving(true);
		    console.log(data);
		    self.start_at_changed_for.push(data.name() + '-' + data.start_at());
        };

		self.filesViewModel.addToScheduledJobs = function(data) {
		    self.needs_saving(true);
			self.settingsViewModel.settings.plugins.printscheduler.scheduled_jobs.push({name: ko.observable(data["name"]), path: ko.observable(data["path"]), start_at: ko.observable("")});
		};

		self.removeJob = function(data) {
		    self.needs_saving(true);
		    self.settingsViewModel.settings.plugins.printscheduler.scheduled_jobs.remove(data);
            self.settingsViewModel.settings.plugins.printscheduler.scheduled_jobs_need_saving = true;
		    self.settingsViewModel.saveData();
        };

		self.removeAllJobs = function() {
		    self.needs_saving(true);
		    self.settingsViewModel.settings.plugins.printscheduler.scheduled_jobs.removeAll();
            self.settingsViewModel.settings.plugins.printscheduler.scheduled_jobs_need_saving = true;
		    self.settingsViewModel.saveData();
        };

		self.saveScheduledJobs = function() {
            self.settingsViewModel.settings.plugins.printscheduler.scheduled_jobs_need_saving = true;
		    self.settingsViewModel.saveData();
        };

		self.onEventSettingsUpdated = function() {
		    self.needs_saving(false);
		    self.settingsViewModel.settings.plugins.printscheduler.scheduled_jobs_need_saving = false;
		    self.start_at_changed_for.removeAll();
        };

		$(document).ready(function() {
			let regex = /<div class="btn-group action-buttons">([\s\S]*)<.div>/mi;
			let template = '<div class="btn btn-mini" data-bind="click: function() { if ($root.loginState.isUser()) { $root.addToScheduledJobs($data) } else { return; } }, css: {disabled: !$root.loginState.isUser()}" title="Add to Print Scheduler"><i class="fa fa-clock-o"></i></div>';

			$("#files_template_machinecode").text(function () {
				return $(this).text().replace(regex, '<div class="btn-group action-buttons">$1	' + template + '></div>');
			});
        });
    }

    OCTOPRINT_VIEWMODELS.push({
        construct: PrintschedulerViewModel,
        dependencies: ["settingsViewModel", "filesViewModel"],
        elements: ["#tab_plugin_printscheduler", "#settings_plugin_printscheduler"]
    });
});
