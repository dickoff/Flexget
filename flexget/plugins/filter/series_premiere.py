from __future__ import unicode_literals, division, absolute_import
from flexget.plugin import register_plugin, priority, get_plugin_by_name
from flexget.plugins.filter.series import FilterSeriesBase, normalize_series_name


class FilterSeriesPremiere(FilterSeriesBase):
    """
    Accept an entry that appears to be the first episode of any series.

    Can be configured with any of the options of series plugin
    Examples:

    series_premiere: yes

    series_premiere:
      path: ~/Media/TV/_NEW_/.
      quality: 720p
      timeframe: 12 hours

    NOTE: this plugin only looks in the entry title and expects the title
    format to start with the series name followed by the episode info. Use
    the manipulate plugin to modify the entry title to match this format, if
    necessary.

    TODO:
        - integrate thetvdb to allow refining by genres, etc.
    """

    def validator(self):
        from flexget import validator
        root = validator.factory()
        # Accept yes to just turn on
        root.accept('boolean')
        options = root.accept('dict')
        self.build_options_validator(options)
        options.accept('boolean', key='allow_seasonless')
        return root

    # Run after series and metainfo series plugins
    @priority(115)
    def on_task_metainfo(self, task, config):
        if not config:
            # Don't run when we are disabled
            return
        # Generate the group settings for series plugin
        group_settings = {}
        allow_seasonless = False
        if isinstance(config, dict):
            allow_seasonless = config.pop('allow_seasonless', False)
            group_settings = config
        # Generate a list of unique series that have premieres
        metainfo_series = get_plugin_by_name('metainfo_series')
        guess_entry = metainfo_series.instance.guess_entry
        # Make a set of unique series according to series name normalization rules
        guessed_series = {}
        for entry in task.entries:
            if guess_entry(entry, allow_seasonless=allow_seasonless):
                if entry['series_season'] == 1 and entry['series_episode'] in (0, 1):
                    guessed_series.setdefault(normalize_series_name(entry['series_name']), entry['series_name'])
        # Reject any further episodes in those series
        for entry in task.entries:
            for series in guessed_series.itervalues():
                if entry.get('series_name') == series and not (
                        entry.get('series_season') == 1
                        and entry.get('series_episode') in (0, 1)):
                    entry.reject('Non premiere episode in a premiere series')
        # Combine settings and series into series plugin config format
        allseries = {'settings': {'series_premiere': group_settings}, 'series_premiere': guessed_series.values()}
        # Merge the our config in to the main series config
        self.merge_config(task, allseries)


register_plugin(FilterSeriesPremiere, 'series_premiere', api_ver=2)
