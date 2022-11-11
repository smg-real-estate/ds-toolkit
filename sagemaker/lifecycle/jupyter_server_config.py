c.ServerApp.kernel_spec_manager_class='environment_kernels.EnvironmentKernelSpecManager'
c.ServerApp.login_handler_class='sagemaker_nbi_agent.jupyter_overrides.login_handler.SageMakerNotebookLoginHandler'
c.EnvironmentKernelSpecManager.blacklist_envs=['conda_jupytersystemenv', 'conda_anaconda3', 'conda_r', 'conda_r_r']
c.EnvironmentKernelSpecManager.display_name_template='{}'
c.KernelSpecManager.ensure_native_kernel=False
