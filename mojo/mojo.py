import mujoco.viewer
import numpy as np
from dm_control import mjcf

from mojo.elements.body import Body
from mojo.elements.element import MujocoElement
from mojo.elements.model import MujocoModel


class Mojo:
    def __init__(self, base_model_path: str, timestep: float = 0.01):
        model_mjcf = mjcf.from_path(base_model_path)
        self.root_element = MujocoModel(self, model_mjcf)
        self._texture_store: dict[str, mjcf.Element] = {}
        self._dirty = True
        self._passive_dirty = False
        self._passive_viewer_handle = None
        self.set_timestep(timestep)

    def _create_physics_from_model(self):
        self._physics = mjcf.Physics.from_mjcf_model(self.root_element.mjcf)
        self._physics.legacy_step = False
        self._dirty = False

    @property
    def physics(self):
        if self._dirty:
            self._create_physics_from_model()
        return self._physics

    @property
    def model(self):
        if self._dirty:
            self._create_physics_from_model()
        return self._physics.model.ptr

    @property
    def data(self):
        if self._dirty:
            self._create_physics_from_model()
        return self._physics.data.ptr

    def set_timestep(self, timestep: float):
        self.root_element.mjcf.compiler.lengthrange.timestep = timestep

    def launch_viewer(self, passive: bool = False) -> None:
        if self._dirty:
            self._create_physics_from_model()
        if passive:
            self._passive_dirty = False
            self._passive_viewer_handle = mujoco.viewer.launch_passive(
                self._physics.model.ptr, self._physics.data.ptr
            )
        else:
            mujoco.viewer.launch(self._physics.model.ptr, self._physics.data.ptr)

    def sync_passive_viewer(self):
        if self._passive_viewer_handle is None:
            raise RuntimeError("You do not have a passive viewer running.")
        if self._passive_dirty:
            self._passive_dirty = False
            self._create_physics_from_model()
            self._passive_viewer_handle._sim().load(
                self._physics.model.ptr, self._physics.data.ptr, ""
            )
        self._passive_viewer_handle.sync()

    def close_passive_viewer(self):
        if self._passive_viewer_handle is None:
            raise RuntimeError("You do not have a passive viewer running.")
        self._passive_viewer_handle.close()

    def mark_dirty(self):
        self._passive_dirty = True
        self._dirty = True

    def step(self):
        if self._dirty:
            self._create_physics_from_model()
        pass

    def get_material(self, path: str) -> mjcf.Element:
        return self._texture_store.get(path, None)

    def store_material(self, path: str, material_mjcf: mjcf.Element) -> mjcf.Element:
        self._texture_store[path] = material_mjcf

    def load_model(self, path: str, parent: MujocoElement = None):
        model_mjcf = mjcf.from_path(path)
        attach_site = self.root_element.mjcf if parent is None else parent
        attached_model_mjcf = attach_site.attach(model_mjcf)
        self.mark_dirty()
        return Body(self, attached_model_mjcf)

    def set_headlight(
        self,
        active: bool = True,
        ambient: np.ndarray = None,
        diffuse: np.ndarray = None,
        specular: np.ndarray = None,
    ):
        ambient = np.array([0.1, 0.1, 0.1]) if ambient is None else ambient
        diffuse = np.array([0.4, 0.4, 0.4]) if diffuse is None else diffuse
        specular = np.array([0.5, 0.5, 0.5]) if specular is None else specular
        self.root_element.mjcf.visual.headlight.ambient = ambient
        self.root_element.mjcf.visual.headlight.diffuse = diffuse
        self.root_element.mjcf.visual.headlight.specular = specular
        self.root_element.mjcf.visual.headlight.active = active
        self.mark_dirty()

    def __str__(self):
        return self.root_element.mjcf.to_xml_string()