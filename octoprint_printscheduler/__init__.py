# coding=utf-8
import octoprint.plugin
import os
from octoprint.util import RepeatedTimer
from octoprint.events import Events
from octoprint.util import dict_merge
from datetime import datetime
from backports.datetime_fromisoformat import MonkeyPatch

try:
    test = datetime.fromisoformat
except AttributeError:
    MonkeyPatch.patch_fromisoformat()

class PrintschedulerPlugin(octoprint.plugin.SettingsPlugin,
                           octoprint.plugin.AssetPlugin,
                           octoprint.plugin.TemplatePlugin,
                           octoprint.plugin.StartupPlugin,
                           octoprint.plugin.EventHandlerPlugin
                           ):

    def __init__(self):
        super().__init__()
        self.repeated_timer = None
        self.job_active = False

    # ~~ Print Scheduler Functions

    def start_timer(self):
        if self.repeated_timer is None:
            self._logger.debug("Starting repeated timer.")
            self.repeated_timer = RepeatedTimer(60, self.check_scheduled_jobs)
            self.repeated_timer.start()

    def check_scheduled_jobs(self):
        self._logger.debug("Looping through scheduled jobs.")
        scheduled_jobs = self._settings.get(["scheduled_jobs"])
        for job in scheduled_jobs:
            if datetime.fromisoformat(job["start_at"]) <= datetime.now() and job["start_at"] != "":
                self._logger.debug("Job found: {}".format(job))
                if self._settings.get(["system_command_before"]):
                    self._logger.debug("Running system command before print.")
                    os.system(self._settings.get(["system_command_before"]))
                if not self._printer.is_operational():
                    self._logger.debug("Bypassing scheduled job as printer is not available yet.")
                    return
                self.job_active = True
                scheduled_jobs.remove(job)
                self._printer.select_file(job["path"], False, tags={"printscheduler"})
                self._printer.commands(self._settings.get(["command_before"]).split('\n'), tags={"printscheduler"})
                self._printer.start_print(tags={"printscheduler"})
                break

        if scheduled_jobs != self._settings.get(["scheduled_jobs"]):
            self._logger.debug("Scheduled jobs changed to: {}".format(scheduled_jobs))
            self._settings.set(["scheduled_jobs"], scheduled_jobs)
            self._settings.set(["scheduled_jobs_need_saving"], scheduled_jobs)
            self._settings.save(trigger_event=True)

    # ~~ StartupPlugin mixin

    def on_after_startup(self):
        self.start_timer()

    # ~~ EventHandlerPlugin mixin

    def on_event(self, event, payload, *args, **kwargs):
        if event not in [Events.PRINT_STARTED, Events.PRINT_DONE, Events.PRINT_CANCELLED, Events.PRINT_FAILED]:
            return

        if event == Events.PRINT_STARTED:
            self._logger.debug("Stopping repeated timer from event: {}.".format(event))
            self.repeated_timer.cancel()
            self.repeated_timer = None

        if event in [Events.PRINT_DONE, Events.PRINT_CANCELLED, Events.PRINT_FAILED]:
            self._logger.debug("Starting repeated timer from event: {}.".format(event))
            if self.job_active:
                self._printer.commands(self._settings.get(["command_after"]).split('\n'), tags={"printscheduler"})
                if self._settings.get(["system_command_after"]):
                    os.system(self._settings.get(["system_command_after"]))
                self.job_active = False
            self.start_timer()

    # ~~ SettingsPlugin mixin

    def get_settings_defaults(self):
        return {
            "command_after": "",
            "command_before": "",
            "system_command_after": "",
            "system_command_before": "",
            "scheduled_jobs": [],
            "theme": "default"
        }

    def on_settings_save(self, data):
        if data.get("scheduled_jobs_need_saving", False) and isinstance(data["scheduled_jobs"], list):
            self._logger.debug("Sorting scheduled jobs from: {}.".format(data["scheduled_jobs"]))
            data["scheduled_jobs"].sort(key=lambda item: datetime.fromisoformat(item.get("start_at")))
            self._logger.debug("Sorting scheduled jobs to: {}.".format(data["scheduled_jobs"]))

        if data.get("scheduled_jobs_need_saving", False):
            data.pop("scheduled_jobs_need_saving")
        octoprint.plugin.SettingsPlugin.on_settings_save(self, dict_merge(self._settings.get([], merged=True), data))

    # ~~ AssetPlugin mixin

    def get_assets(self):
        return {
            "js": ["js/jquery.datetimepicker.full.min.js", "js/ko.datetimepicker.js", "js/printscheduler.js"],
            "css": ["css/jquery.datetimepicker.min.css", "css/printscheduler.css"]
        }

    # ~~ TemplatePlugin mixin

    def get_template_vars(self):
        return {"plugin_version": self._plugin_version}

    def get_template_configs(self):
        return [{"type": "tab", "custom_bindings": True}, {"type": "settings", "custom_bindings": True}]

    # ~~ Softwareupdate hook

    def get_update_information(self):
        return {
            "printscheduler": {
                "displayName": "Print Scheduler",
                "displayVersion": self._plugin_version,
                "type": "github_release",
                "user": "jneilliii",
                "repo": "OctoPrint-PrintScheduler",
                "current": self._plugin_version,
                "stable_branch": {"name": "Stable", "branch": "master", "comittish": ["master"]},
                "prerelease_branches": [{"name": "Release Candidate", "branch": "rc", "comittish": ["rc", "master"]}],
                "pip": "https://github.com/jneilliii/OctoPrint-PrintScheduler/archive/{target_version}.zip",
            }
        }


__plugin_name__ = "Print Scheduler"
__plugin_pythoncompat__ = ">=3,<4"  # only python 3


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = PrintschedulerPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
