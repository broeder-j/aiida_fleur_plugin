# -*- coding: utf-8 -*-
###############################################################################
# Copyright (c), Forschungszentrum Jülich GmbH, IAS-1/PGI-1, Germany.         #
#                All rights reserved.                                         #
# This file is part of the AiiDA-FLEUR package.                               #
#                                                                             #
# The code is hosted on GitHub at https://github.com/JuDFTteam/aiida-fleur    #
# For further information on the license, see the LICENSE.txt file            #
# For further information please visit http://www.flapw.de or                 #
# http://aiida-fleur.readthedocs.io/en/develop/                               #
###############################################################################
'''
Module with CLI commands to launch for calcjob and workflows of aiida-fleur.

# TODO: these launch commands should be put in seperate files, if this one becomes to large..
'''
import click
from . import cmd_launch
from ..util import options
from ..util.utils import launch_process
from ..util import defaults
#from ..util.defaults import si_structure
from aiida_fleur.tools.dict_util import clean_nones
from aiida.orm import Code, load_node, Dict
from aiida.plugins import WorkflowFactory
from aiida.plugins import CalculationFactory


@cmd_launch.command('inpgen')
@options.STRUCTURE_OR_FILE(default=defaults.get_si_bulk_structure, show_default=True)
@options.INPGEN()
@options.CALC_PARAMETERS()
@options.SETTINGS()
@options.DAEMON()
def launch_inpgen(structure, inpgen, calc_parameters, daemon, settings):  #, num_machines, wallclock_seconds, daemon):
    """
    Launch an inpgen calcjob on given input

    If no code is given it queries the DB for inpgen codes and uses the one with
    the newest creation time.

    Either structure or anysource_structure can be specified.
    Default structure is Si bulk.
    """

    process_class = CalculationFactory('fleur.inpgen')
    inputs = {
        'code': inpgen,
        'structure': structure,
        'parameters': calc_parameters,
        'settings': settings,
        'metadata': {
            'options': {
                'withmpi': False,
                'max_wallclock_seconds': 6000,
                'resources': {
                    'num_machines': 1,
                    'num_mpiprocs_per_machine': 1,
                }
            }
        }
    }
    inputs = clean_nones(inputs)
    builder = process_class.get_builder()
    builder.update(inputs)
    launch_process(builder, daemon)


@cmd_launch.command('fleur')
@options.FLEURINP()
@options.FLEUR()
@options.REMOTE()
@options.SETTINGS()
@options.DAEMON()
@options.MAX_NUM_MACHINES()
@options.MAX_WALLCLOCK_SECONDS()
@options.NUM_MPIPROCS_PER_MACHINE()
@options.OPTION_NODE()
@options.WITH_MPI()
@click.option('--launch_base/--no-launch_base',
              is_flag=True,
              default=True,
              show_default=True,
              help=('Run the base_fleur workchain, which also handles errors instead '
                    'of a single fleur calcjob.'))
def launch_fleur(fleurinp, fleur, parent_folder, daemon, launch_base, settings, max_num_machines,
                 num_mpiprocs_per_machine, max_wallclock_seconds, with_mpi, option_node):
    """
    Launch a base_fleur workchain.
    If launch_base is False launch a single fleur calcjob instead.

    """

    process_class = CalculationFactory('fleur.fleur')
    workchain_class = WorkflowFactory('fleur.base')

    inputs = {
        'code': fleur,
        'fleurinpdata': fleurinp,
        'parent_folder': parent_folder,
        'settings': settings,
        'metadata': {
            'options': {
                'withmpi': with_mpi,
                'max_wallclock_seconds': max_wallclock_seconds,
                'resources': {
                    'num_machines': max_num_machines,
                    'num_mpiprocs_per_machine': num_mpiprocs_per_machine,
                }
            }
        }
    }

    if not launch_base:
        inputs = clean_nones(inputs)
        builder = process_class.get_builder()
        builder.update(inputs)
    else:
        if option_node is None:
            option_node = Dict(
                dict={
                    'withmpi': with_mpi,
                    'max_wallclock_seconds': max_wallclock_seconds,
                    'resources': {
                        'num_machines': max_num_machines,
                        'num_mpiprocs_per_machine': num_mpiprocs_per_machine
                    }
                })

        inputs_base = {
            'code': fleur,
            'fleurinpdata': fleurinp,
            'parent_folder': parent_folder,
            'settings': settings,
            'options': option_node
        }
        inputs_base = clean_nones(inputs_base)
        builder = workchain_class.get_builder()
        builder.update(**inputs_base)

    launch_process(builder, daemon)


@cmd_launch.command('scf')
@options.STRUCTURE_OR_FILE(default=defaults.get_si_bulk_structure, show_default=True)
@options.INPGEN()
@options.CALC_PARAMETERS()
@options.SETTINGS()
@options.FLEURINP()
@options.FLEUR()
@options.WF_PARAMETERS()
@options.REMOTE()
@options.SETTINGS()
@options.DAEMON()
@options.OPTION_NODE()
def launch_scf(structure, inpgen, calc_parameters, fleurinp, fleur, wf_parameters, parent_folder, daemon, settings,
               option_node):
    """
    Launch a scf workchain
    """
    workchain_class = WorkflowFactory('fleur.scf')
    inputs = {
        'structure': structure,
        'fleurinpdata': fleurinp,
        'wf_parameters': wf_parameters,
        'calc_parameters': calc_parameters,
        'remote_data': parent_folder,
        'settings': settings,
        'options': option_node
    }
    if inpgen is not None:
        inputs['inpgen'] = load_node(inpgen)
    inputs = clean_nones(inputs)
    builder = workchain_class.get_builder(code=load_node(fleur))
    builder.update(inputs)
    launch_process(builder, daemon)


@cmd_launch.command('relax')
@options.STRUCTURE_OR_FILE(default=defaults.get_si_bulk_structure, show_default=True)
@options.INPGEN()
@options.CALC_PARAMETERS()
@options.SETTINGS()
@options.FLEUR()
@options.WF_PARAMETERS()
@options.SCF_PARAMETERS()
@options.DAEMON()
@options.OPTION_NODE()
def launch_relax(structure, inpgen, calc_parameters, fleur, wf_parameters, scf_parameters, daemon, settings,
                 option_node):
    """
    Launch a base relax workchain

    # TODO final scf input
    """
    workchain_class = WorkflowFactory('fleur.base_relax')
    inputs = {
        'scf': {
            'wf_parameters': scf_parameters,
            'structure': structure,
            'calc_parameters': calc_parameters,
            'options': option_node,
            'inpgen': inpgen,
            'fleur': fleur
        },
        'wf_parameters': wf_parameters
    }
    inputs = clean_nones(inputs)
    builder = workchain_class.get_builder()
    builder.update(inputs)
    launch_process(builder, daemon)


@cmd_launch.command('eos')
@options.STRUCTURE_OR_FILE(default=defaults.get_si_bulk_structure, show_default=True)
@options.INPGEN()
@options.CALC_PARAMETERS()
@options.SETTINGS()
@options.FLEUR()
@options.WF_PARAMETERS()
@options.SCF_PARAMETERS()
@options.DAEMON()
@options.OPTION_NODE()
def launch_eos(structure, inpgen, calc_parameters, fleur, wf_parameters, scf_parameters, daemon, settings, option_node):
    """
    Launch a eos workchain
    """
    workchain_class = WorkflowFactory('fleur.eos')
    inputs = {
        'scf': {
            'wf_parameters': scf_parameters,
            'calc_parameters': calc_parameters,
            'options': option_node,
            'inpgen': inpgen,
            'fleur': fleur
        },
        'wf_parameters': wf_parameters,
        'structure': structure
    }
    inputs = clean_nones(inputs)
    builder = workchain_class.get_builder()
    builder.update(inputs)
    launch_process(builder, daemon)


@cmd_launch.command('banddos')
@options.FLEURINP()
@options.FLEUR()
@options.WF_PARAMETERS()
@options.REMOTE()
@options.DAEMON()
@options.OPTION_NODE()
def launch_banddos(fleurinp, fleur, wf_parameters, parent_folder, daemon, settings, option_node):
    """
    Launch a banddos workchain
    """
    click.echo('Not implemented yet, sorry. Please implement me!')
    workchain_class = WorkflowFactory('fleur.banddos')
    inputs = {
        'wf_parameters': wf_parameters,
        'fleur': fleur,
        'remote': parent_folder,
        'fleurinp': fleurinp,
        'options': option_node
    }
    inputs = clean_nones(inputs)
    builder = workchain_class.get_builder()
    builder.update(inputs)
    launch_process(builder, daemon)


@cmd_launch.command('init_cls')
@options.STRUCTURE_OR_FILE(default=defaults.get_si_bulk_structure, show_default=True)
@options.INPGEN()
@options.CALC_PARAMETERS()
@options.SETTINGS()
@options.FLEURINP()
@options.FLEUR()
@options.WF_PARAMETERS()
@options.DAEMON()
@options.OPTION_NODE()
def launch_init_cls(structure, inpgen, calc_parameters, fleurinp, fleur, wf_parameters, daemon, settings, option_node):
    """
    Launch an init_cls workchain
    """
    click.echo('Not implemented yet, sorry. Please implement me!')
    workchain_class = WorkflowFactory('fleur.init_cls')
    inputs = {
        'calc_parameters': calc_parameters,
        'options': option_node,
        'inpgen': inpgen,
        'fleur': fleur,
        'wf_parameters': wf_parameters,
        'structure': structure
    }
    inputs = clean_nones(inputs)
    builder = workchain_class.get_builder()
    builder.update(inputs)
    launch_process(builder, daemon)


@cmd_launch.command('corehole')
@options.STRUCTURE_OR_FILE(default=defaults.get_si_bulk_structure, show_default=True)
@options.INPGEN()
@options.CALC_PARAMETERS()
@options.SETTINGS()
@options.FLEURINP()
@options.FLEUR()
@options.WF_PARAMETERS()
@options.DAEMON()
@options.OPTION_NODE()
def launch_corehole(structure, inpgen, calc_parameters, fleurinp, fleur, wf_parameters, daemon, settings, option_node):
    """
    Launch a corehole workchain
    """
    click.echo('Not implemented yet, sorry. Please implement me!')
    workchain_class = WorkflowFactory('fleur.corehole')
    inputs = {
        'calc_parameters': calc_parameters,
        'options': option_node,
        'inpgen': inpgen,
        'fleur': fleur,
        'wf_parameters': wf_parameters,
        'structure': structure
    }
    inputs = clean_nones(inputs)
    builder = workchain_class.get_builder()
    builder.update(inputs)
    launch_process(builder, daemon)


@cmd_launch.command('mae')
@options.STRUCTURE_OR_FILE(default=defaults.get_si_bulk_structure, show_default=True)
@options.INPGEN()
@options.CALC_PARAMETERS()
@options.SETTINGS()
@options.FLEURINP()
@options.FLEUR()
@options.WF_PARAMETERS()
@options.REMOTE()
@options.DAEMON()
@options.OPTION_NODE()
def launch_mae(structure_or_file, inpgen, calc_parameters, fleurinp, fleur, wf_parameter, remote, daemon, settings,
               option_node):
    """
    Launch a mae workchain
    """
    click.echo('Not implemented yet, sorry. Please implement me!')
    #workchain_class = WorkflowFactory('fleur.mae')
    #inputs = {}
    #builder = workchain_class.get_builder(code=load_node(fleur),**inputs)
    #launch_process(builder, daemon)


@cmd_launch.command('ssdisp')
def launch_ssdisp():
    """
    Launch a ssdisp workchain
    """
    click.echo('Not implemented yet, sorry. Please implement me!')
    #workchain_class = WorkflowFactory('fleur.ssdisp')
    #inputs = {}
    #builder = workchain_class.get_builder(code=load_node(fleur),**inputs)
    #launch_process(builder, daemon)


@cmd_launch.command('dmi')
def launch_dmi():
    """
    Launch a dmi workchain
    """
    click.echo('Not implemented yet, sorry. Please implement me!')
    #workchain_class = WorkflowFactory('fleur.dmi')
    #inputs = {}
    #builder = workchain_class.get_builder(code=load_node(fleur),**inputs)
    #launch_process(builder, daemon)


@cmd_launch.command('create_magnetic')
def launch_create_magnetic():
    """
    Launch a create_magnetic workchain
    """
    click.echo('Not implemented yet, sorry. Please implement me!')
    #workchain_class = WorkflowFactory('fleur.create_magnetic')
    #inputs = {}
    #builder = workchain_class.get_builder(code=load_node(fleur),**inputs)
    #launch_process(builder, daemon)
