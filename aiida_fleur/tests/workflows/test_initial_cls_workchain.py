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

# Here we test if the interfaces of the workflows are still the same
from __future__ import absolute_import
from __future__ import print_function

import pytest
import aiida_fleur
import os
from aiida_fleur.workflows.initial_cls import fleur_initial_cls_wc
from aiida.engine import run_get_node

#aiida_path = os.path.dirname(aiida_fleur.__file__)
#TEST_INP_XML_PATH = os.path.join(aiida_path, 'tests/files/inpxml/Si/inp.xml')
#CALC_ENTRY_POINT = 'fleur.fleur'

def clear_spec():
    if hasattr(FleurScfWorkChain, '_spec'):
        # we require this as long we have mutable types as defaults, see aiidateam/aiida-core#3143
        # otherwise we will run into DbNode matching query does not exist
        del FleurScfWorkChain._spec
    if hasattr(FleurBaseWorkChain, '_spec'):
        # we require this as long we have mutable types as defaults, see aiidateam/aiida-core#3143
        # otherwise we will run into DbNode matching query does not exist
        del FleurBaseWorkChain._spec

# tests
@pytest.mark.usefixtures("aiida_profile", "clear_database")
class Test_fleur_initial_cls_wc():
    """
    Regression tests for the fleur_initial_cls_wc
    """
    @pytest.mark.timeout(500, method='thread')
    def test_fleur_initial_cls_W(self, run_with_cache, inpgen_local_code, fleur_local_code,
                                 generate_structure_W):
        """
        full example using fleur_initial_cls_wc with just elemental W as input
        (W, onw atoms per unit cell)
        uses the same structure as reference.
        """
        from aiida.orm import Code, load_node, Dict, StructureData

        options = {'resources': {"num_machines": 1, "num_mpiprocs_per_machine": 1},
                   'max_wallclock_seconds': 5 * 60,
                   'withmpi': False, 'custom_scheduler_commands': ''}

        parameters = Dict(dict={
                  'atom':{
                        'element' : 'W',
                        'jri' : 833,
                        'rmt' : 2.3,
                        'dx' : 0.015,
                        'lmax' : 8,
                        'lo' : '5p',
                        'econfig': '[Kr] 5s2 4d10 4f14| 5p6 5d4 6s2',
                        },
                  'comp': {
                        'kmax': 3.0,
                        },
                  'kpt': {
                        'nkpt': 100,
                        }}).store()

        structure = generate_structure_W().store()
        wf_para = Dict(dict={'references' : {'W' : [structure.uuid, parameters.uuid]}})


        FleurCode = fleur_local_code
        InpgenCode = inpgen_local_code

        # create process builder to set parameters
        inputs = {
            'metadata' : {
                'description' : 'Simple fleur_initial_cls_wc test with W bulk',
                'label' : 'fleur_initial_cls_wc_test_W_bulk'},
        'options' :  Dict(dict=options),
        'fleur' : FleurCode,
        'inpgen' : InpgenCode,
        'wf_parameters' : wf_para,
        'calc_parameters' : parameters,
        'structure' : structure
        }

        # now run calculation
        out, node = run_with_cache(inputs, process_class=fleur_initial_cls_wc)


        # check general run
        assert node.is_finished_ok

        # check output
        # corelevel shift should be zero
        outn = out.get('output_initial_cls_wc_para', None)
        assert outn != None
        outd = outn.get_dict()

        assert outd.get('successful')
        assert outd.get('warnings') == []
        assert outd.get('corelevelshifts') == {"W":
               [[0.0, 0.0, 0.0,0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]]}

        assert outd.get('formation_energy') == [0.0]

    @pytest.mark.skip(reason="Test is not implemented")
    @pytest.mark.timeout(500, method='thread')
    def test_fleur_initial_cls_wc_binary_with_given_ref(self, run_with_cache, mock_code_factory):
        """
        Full regression test of fleur_initial_cls_wc starting with a crystal structure and parameters
        """
        assert False

    @pytest.mark.skip(reason="Test is not implemented")
    @pytest.mark.timeout(500, method='thread')
    def test_fleur_initial_cls_wc_validation_wrong_inputs(self, run_with_cache, mock_code_factory):
        """
        Test the validation behavior of fleur_initial_cls_wc if wrong input is provided it should throw
        an exitcode and not start a Fleur run or crash
        """
        assert False
