from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from optimizer_profiler import select, console_table


def row(name, fps, worst, size, status='passed'):
    return dict(candidate=name,status=status,display=dict(displayed_fps=fps,p95_ms=worst,worst_ms=worst),
                crt_bytes=size,profile=dict(mean_render_cycles=100))


class OptimizerSelection(unittest.TestCase):
    def test_highest_average_wins_and_reports_worse_tail(self):
        rows=[row('v4',7,150,800),row('fast-spikes',8,180,600),row('v2',7.5,140,650)]
        choice=select(rows,'v4')
        self.assertEqual(choice['winner'],'fast-spikes')
        self.assertEqual(choice['fastest_measured'],'fast-spikes')
        self.assertFalse(rows[1]['tail_gate_passed'])

    def test_failure_or_capacity_cannot_win(self):
        rows=[row('v4',7,150,800),row('bad-pixels',50,20,100,'failed'),row('too-large',60,10,50,'capacity')]
        self.assertEqual(select(rows,'v4')['winner'],'v4')
        self.assertIsNone(select(rows,'bad-pixels')['winner'])

    def test_near_tie_does_not_relabel_slower_cart_as_fps_winner(self):
        rows=[row('v4',7,150,800),row('tiny-gain',7.01,150,850)]
        choice=select(rows,'v4')
        self.assertEqual(choice['winner'],'tiny-gain')
        self.assertEqual(len(choice['near_ties']),2)
        self.assertFalse(choice['automatically_promoted'])

    def test_terminal_marks_fps_winner_and_keeps_na(self):
        rows=[row('slow',7,150,100),row('fast',8,140,200)]
        for r in rows:r['method']=r['candidate']
        text=console_table(rows)
        self.assertIn('WINNER',text)
        self.assertIn('8.00000',text)
        self.assertNotIn('\033[',text)
        self.assertIn('\033[1;32m',console_table(rows,color=True))

    def test_config_and_cli_override_and_unsupported_options(self):
        import tempfile
        from c643d.toolchain import load_toolchain_settings
        from c643d.cli import make_parser
        from c643d.renderer_contest import validate
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'c643d.ini'
            p.write_text('[render_defaults]\nrenderer_selection=best-fps\n')
            parser=make_parser(load_toolchain_settings(p))
            base=['build','--scene','scene.c643dscene','--contest-out',str(Path(folder)/'out')]
            args=parser.parse_args(base);self.assertEqual(args.renderer_selection,'best-fps');validate(args)
            self.assertEqual(parser.parse_args(base+['--renderer-selection','manual']).renderer_selection,'manual')
            with self.assertRaisesRegex(ValueError,'unsupported overrides'):
                validate(parser.parse_args(base+['--color','red']))
            p.write_text('[render_defaults]\nrenderer_selection=best-fps\n[cartridge_defaults]\ncart_type=gmod3\n')
            settings=load_toolchain_settings(p); configured=make_parser(settings)
            with self.assertRaisesRegex(ValueError,'EasyFlash'):
                validate(configured.parse_args(base),settings)
            validate(configured.parse_args(base+['--cart-type','easyflash']),settings)
            p.write_text('[toolchain]\nvice_args=-ntsc\n')
            settings=load_toolchain_settings(p)
            with self.assertRaisesRegex(ValueError,'configured vice_args'):
                validate(make_parser(settings).parse_args(base),settings)
            p.write_text('[render_defaults]\nrenderer_selection=magic\n')
            with self.assertRaises(ValueError):load_toolchain_settings(p)

if __name__=='__main__':unittest.main()
